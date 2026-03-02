"""EcoChain AI — Gemini LLM Client with Retry & Fallback.

Client asynchrone pour Google Gemini avec :
- Retry exponentiel (3 tentatives, backoff 1s/2s/4s)
- Fallback automatique de Gemini 2.5 Flash vers Gemini 1.5 Flash
- Parsing de réponses JSON structurées
- Gestion gracieuse des erreurs API (quota, timeout, 5xx)
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any

import google.generativeai as genai
from google.generativeai.types import GenerateContentResponse
from pydantic import ConfigDict
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class LLMSettings(BaseSettings):
    """Configuration du client LLM via variables d'environnement.

    Attributes:
        google_api_key: Clé API Google AI Studio.
        gemini_primary_model: Modèle principal (défaut: gemini-2.5-flash).
        gemini_fallback_model: Modèle de fallback (défaut: gemini-1.5-flash).
        llm_max_retries: Nombre maximum de tentatives (défaut: 3).
        llm_retry_base_delay: Délai de base pour le backoff exponentiel en secondes.
    """

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # Ignorer les variables .env non déclarées (API_HOST, etc.)
    )

    google_api_key: str = ""
    gemini_primary_model: str = "gemini-2.5-flash"
    gemini_fallback_model: str = "gemini-1.5-flash"
    llm_max_retries: int = 3
    llm_retry_base_delay: float = 1.0


@dataclass
class GeminiResponse:
    """Réponse structurée du client Gemini.

    Attributes:
        content: Contenu textuel de la réponse.
        model_used: Modèle effectivement utilisé.
        was_fallback: True si le modèle de fallback a été utilisé.
        raw_response: Réponse brute de l'API.
    """

    content: str
    model_used: str
    was_fallback: bool = False
    raw_response: Any = field(default=None, repr=False)


class GeminiClientError(Exception):
    """Erreur du client Gemini après épuisement des retries."""

    def __init__(self, message: str, model: str, attempts: int) -> None:
        self.model = model
        self.attempts = attempts
        super().__init__(message)


class GeminiClient:
    """Client asynchrone pour Google Gemini avec retry exponentiel et fallback.

    Gère automatiquement les erreurs API en basculant du modèle primaire
    (Gemini 2.5 Flash) vers le modèle de fallback (Gemini 1.5 Flash)
    avec retry exponentiel (backoff 1s, 2s, 4s).

    Attributes:
        settings: Configuration LLM.
        _primary_model: Instance du modèle principal.
        _fallback_model: Instance du modèle de fallback.
        _is_configured: Flag indiquant si l'API est configurée.
    """

    def __init__(self, settings: LLMSettings | None = None) -> None:
        """Initialise le client Gemini.

        Args:
            settings: Configuration LLM. Si None, charge depuis l'environnement.
        """
        self.settings = settings or LLMSettings()
        self._is_configured = False
        self._primary_model: genai.GenerativeModel | None = None
        self._fallback_model: genai.GenerativeModel | None = None
        self._configure()

    def _configure(self) -> None:
        """Configure le SDK Google Generative AI avec la clé API.

        Raises:
            ValueError: Si GOOGLE_API_KEY n'est pas définie.
        """
        api_key = self.settings.google_api_key or os.getenv("GOOGLE_API_KEY", "")
        if not api_key:
            logger.warning(
                "GOOGLE_API_KEY non définie. Le client fonctionnera en mode dégradé."
            )
            return

        genai.configure(api_key=api_key)
        self._primary_model = genai.GenerativeModel(self.settings.gemini_primary_model)
        self._fallback_model = genai.GenerativeModel(self.settings.gemini_fallback_model)
        self._is_configured = True
        logger.info(
            "Client Gemini configuré — Primary: %s, Fallback: %s",
            self.settings.gemini_primary_model,
            self.settings.gemini_fallback_model,
        )

    @property
    def is_ready(self) -> bool:
        """Indique si le client est configuré et prêt à l'emploi."""
        return self._is_configured

    async def _call_model(
        self,
        model: genai.GenerativeModel,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float = 0.2,
    ) -> GenerateContentResponse:
        """Appelle un modèle Gemini de manière asynchrone.

        Args:
            model: Instance du modèle à appeler.
            prompt: Prompt utilisateur.
            system_instruction: Instruction système optionnelle.
            temperature: Température de génération (0-1).

        Returns:
            Réponse brute de l'API Gemini.

        Raises:
            Exception: Toute erreur API propagée pour gestion par le retry.
        """
        generation_config = genai.GenerationConfig(
            temperature=temperature,
            top_p=0.95,
            max_output_tokens=8192,
        )

        # Recréer le modèle avec system_instruction si fourni
        if system_instruction:
            model = genai.GenerativeModel(
                model_name=model.model_name,
                system_instruction=system_instruction,
                generation_config=generation_config,
            )

        # Exécution asynchrone via asyncio
        loop = asyncio.get_event_loop()
        response: GenerateContentResponse = await loop.run_in_executor(
            None,
            lambda: model.generate_content(
                prompt,
                generation_config=generation_config,
            ),
        )
        return response

    async def _retry_with_backoff(
        self,
        model: genai.GenerativeModel,
        model_name: str,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float = 0.2,
    ) -> GenerateContentResponse:
        """Exécute un appel avec retry exponentiel.

        Backoff pattern: 1s, 2s, 4s (base_delay * 2^attempt).

        Args:
            model: Instance du modèle.
            model_name: Nom du modèle pour le logging.
            prompt: Prompt utilisateur.
            system_instruction: Instruction système optionnelle.
            temperature: Température de génération.

        Returns:
            Réponse brute de l'API Gemini.

        Raises:
            GeminiClientError: Si toutes les tentatives échouent.
        """
        last_error: Exception | None = None

        for attempt in range(self.settings.llm_max_retries):
            try:
                logger.debug(
                    "Tentative %d/%d sur %s",
                    attempt + 1,
                    self.settings.llm_max_retries,
                    model_name,
                )
                return await self._call_model(
                    model=model,
                    prompt=prompt,
                    system_instruction=system_instruction,
                    temperature=temperature,
                )
            except Exception as e:
                last_error = e
                delay = self.settings.llm_retry_base_delay * (2 ** attempt)
                logger.warning(
                    "Erreur sur %s (tentative %d/%d): %s. Retry dans %.1fs",
                    model_name,
                    attempt + 1,
                    self.settings.llm_max_retries,
                    str(e)[:200],
                    delay,
                )
                if attempt < self.settings.llm_max_retries - 1:
                    await asyncio.sleep(delay)

        raise GeminiClientError(
            message=f"Échec après {self.settings.llm_max_retries} tentatives sur {model_name}: {last_error}",
            model=model_name,
            attempts=self.settings.llm_max_retries,
        )

    async def generate(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float = 0.2,
    ) -> GeminiResponse:
        """Génère une réponse avec retry exponentiel et fallback automatique.

        Flow:
        1. Tente le modèle primaire avec retry (3 tentatives, backoff 1s/2s/4s)
        2. Si échec, bascule sur le modèle fallback avec retry
        3. Si tout échoue, lève GeminiClientError

        Args:
            prompt: Prompt utilisateur complet.
            system_instruction: Instruction système pour configurer le comportement.
            temperature: Température de génération (0 = déterministe, 1 = créatif).

        Returns:
            GeminiResponse avec le contenu et les métadonnées.

        Raises:
            GeminiClientError: Si tous les modèles et retries échouent.
            ValueError: Si le client n'est pas configuré.
        """
        if not self._is_configured or self._primary_model is None:
            raise ValueError(
                "Client Gemini non configuré. Vérifiez GOOGLE_API_KEY dans .env"
            )

        # Tentative sur le modèle primaire
        try:
            response = await self._retry_with_backoff(
                model=self._primary_model,
                model_name=self.settings.gemini_primary_model,
                prompt=prompt,
                system_instruction=system_instruction,
                temperature=temperature,
            )
            return GeminiResponse(
                content=response.text,
                model_used=self.settings.gemini_primary_model,
                was_fallback=False,
                raw_response=response,
            )
        except GeminiClientError:
            logger.warning(
                "Modèle primaire (%s) épuisé. Bascule sur fallback (%s)",
                self.settings.gemini_primary_model,
                self.settings.gemini_fallback_model,
            )

        # Fallback sur le modèle secondaire
        if self._fallback_model is None:
            raise GeminiClientError(
                message="Pas de modèle fallback configuré",
                model="none",
                attempts=0,
            )

        try:
            response = await self._retry_with_backoff(
                model=self._fallback_model,
                model_name=self.settings.gemini_fallback_model,
                prompt=prompt,
                system_instruction=system_instruction,
                temperature=temperature,
            )
            return GeminiResponse(
                content=response.text,
                model_used=self.settings.gemini_fallback_model,
                was_fallback=True,
                raw_response=response,
            )
        except GeminiClientError:
            raise GeminiClientError(
                message=(
                    f"Tous les modèles ont échoué "
                    f"(primary: {self.settings.gemini_primary_model}, "
                    f"fallback: {self.settings.gemini_fallback_model})"
                ),
                model="all",
                attempts=self.settings.llm_max_retries * 2,
            )

    async def generate_json(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float = 0.1,
    ) -> dict[str, Any]:
        """Génère une réponse JSON structurée.

        Ajoute automatiquement l'instruction de format JSON et parse la réponse.

        Args:
            prompt: Prompt utilisateur.
            system_instruction: Instruction système additionnelle.
            temperature: Température basse par défaut pour la cohérence JSON.

        Returns:
            Dictionnaire parsé depuis la réponse JSON.

        Raises:
            GeminiClientError: Si la génération échoue.
            json.JSONDecodeError: Si la réponse n'est pas du JSON valide.
        """
        json_instruction = (
            "Tu DOIS répondre UNIQUEMENT avec du JSON valide. "
            "Pas de texte avant ou après le JSON. "
            "Pas de markdown code blocks. Juste le JSON brut."
        )
        full_system = (
            f"{system_instruction}\n\n{json_instruction}"
            if system_instruction
            else json_instruction
        )

        response = await self.generate(
            prompt=prompt,
            system_instruction=full_system,
            temperature=temperature,
        )

        # Nettoyer la réponse des éventuels markdown code blocks
        content = response.content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        try:
            parsed: dict[str, Any] = json.loads(content)
            return parsed
        except json.JSONDecodeError as e:
            logger.error(
                "Échec parsing JSON de la réponse %s: %s\nContenu: %s",
                response.model_used,
                str(e),
                content[:500],
            )
            raise

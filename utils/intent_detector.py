# intent_detector.py

from azure.ai.language.conversations import ConversationAnalysisClient
from azure.core.credentials import AzureKeyCredential
from constants import Intent
import os

class IntentDetector:
    def __init__(self):
        self.endpoint = os.getenv("AZURE_LANGUAGE_ENDPOINT", "")
        self.key = os.getenv("AZURE_LANGUAGE_KEY", "")
        self.project_name = os.getenv("AZURE_LANGUAGE_PROJECT")
        self.deployment_name = os.getenv("AZURE_LANGUAGE_DEPLOYMENT_NAME")
        try:
            self.client = ConversationAnalysisClient(
                endpoint=self.endpoint,
                credential=AzureKeyCredential(self.key),
                api_version="2024-11-15-preview"  # Ensure to use the correct API version
            )
        except Exception as e:
            raise ValueError(f"Failed to initialize ConversationAnalysisClient: {e}")

    def detect_intent(self, text: str) -> str:
        result = self.client.analyze_conversation(
            task={
                "kind": "Conversation",
                "analysisInput": {
                    "conversationItem": {
                        "participantId": "user",
                        "id": "1",
                        "modality": "text",
                        "language": "en",
                        "text": text
                    },
                    "conversationKind": "conversation"
                },
                "parameters": {
                    "projectName": self.project_name,
                    "deploymentName": self.deployment_name
                }
            }
        )

        prediction = result["result"]["prediction"]
        top_intent = prediction["topIntent"]
        confidence = next((i["confidenceScore"] for i in prediction["intents"] if i["category"] == top_intent), 0)

        if confidence < 0.5:
            return Intent.UNKNOWN

        return top_intent

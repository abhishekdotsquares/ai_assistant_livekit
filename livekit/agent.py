import logging
import requests

from dotenv import load_dotenv
from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli, llm
from livekit.agents.pipeline import VoicePipelineAgent
from livekit.plugins import openai, silero
from livekit.plugins.openai.beta import (
    AssistantCreateOptions,
    AssistantLLM,
    AssistantOptions,
    OnFileUploadedInfo,
)
from typing import AsyncIterable
from livekit.agents import tokenize


load_dotenv()
logger = logging.getLogger("openai_assistant")


def validate_audio(text):
    url = "http://127.0.0.1:5000/get_audio_length"

    data = {
        "text": text
    }

    headers = {
        "Content-Type": "application/json",
    }
    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        response_data = response.json()
        print("Text:", response_data['text'])
        print("Audio Length (seconds):", response_data['audio_length_seconds'])
    else:
        print("Error:", response.json())
    print(response_data['text'], 'reserwrwrwrponse text')
    print(text, 'response text')
    return response_data['text']



async def custom_response(assistant: VoicePipelineAgent, text: str | AsyncIterable[str]):
    full_text = ""
    if type(text) is not str:
        async for chunk in text:
            full_text += chunk
        validated_text = validate_audio(str(full_text))
        validated_text = tokenize.utils.replace_words(
        text=validated_text, replacements={"livekit": r"<<l|aɪ|v|k|ɪ|t|>>"}
        )

        await assistant.say(validated_text, add_to_chat_ctx=True, allow_interruptions=True)
        return ""
    return text

async def entrypoint(ctx: JobContext):
    """This example demonstrates a VoicePipelineAgent that uses OpenAI's Assistant API as the LLM"""
    initial_ctx = llm.ChatContext()

    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    participant = await ctx.wait_for_participant()

    # When you add a ChatMessage that contain images, AssistantLLM will upload them
    # to OpenAI's Assistant API.
    # It's up to you to remove them if desired or otherwise manage them going forward.
    def on_file_uploaded(info: OnFileUploadedInfo):
        logger.info(f"{info.type} uploaded: {info.openai_file_object}")

    agent = VoicePipelineAgent(
        vad=silero.VAD.load(),
        stt=openai.STT(),
        llm=AssistantLLM(
            assistant_opts=AssistantOptions(
                create_options=AssistantCreateOptions(
                    model="gpt-4o",
                    instructions="You are a voice assistant created by LiveKit. Your interface with users will be voice.",
                    name="KITT",
                )
            ),
            on_file_uploaded=on_file_uploaded,
        ),
        tts=openai.TTS(),
        chat_ctx=initial_ctx,
        before_tts_cb=custom_response,
        min_endpointing_delay=0.5,
        max_endpointing_delay=5.0,
    )

    agent.start(ctx.room, participant)
    await agent.say("Hey, how can I help you today?", allow_interruptions=False)


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
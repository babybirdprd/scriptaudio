from google import genai

client = genai.Client()
model_id = "gemini-2.0-flash-exp"
config = {"response_modalities": ["AUDIO"]}  # Specify audio output

async with client.aio.live.connect(model=model_id, config=config) as session:
    message = "Generate speech saying: Hello, this is Gemini 2.0 Flash speaking."
    await session.send(message, end_of_turn=True)
    async for response in session.receive():
        # Handle the audio response here
        print("Received audio response")

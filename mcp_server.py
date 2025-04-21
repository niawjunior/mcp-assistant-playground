from mcp.server.fastmcp import FastMCP
from supabase import create_client, Client
import os
from openai import OpenAI
import asyncio
import base64
from io import BytesIO
from pydub import AudioSegment
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Supabase config
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Init Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Init MCP server
mcp = FastMCP("MCP")


# Create OpenAI client
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


@mcp.tool()
def text_to_speech_gpt4o(text: str, voice: str = "nova", tone: str = "cheerful") -> str:
    """
    Convert input text to speech using GPT-4o TTS and return base64 audio.

    Args:
        text: The text to synthesize.
        voice: One of OpenAI's supported voices (e.g., "nova", "shimmer", "onyx", "echo", "fable", "alloy").
        tone: Instruction to define speech style (e.g., "cheerful", "serious", etc.)

    Returns:
        A base64-encoded audio URL (as a data URI).
    """
    print(f"🎤 [TTS] Generating speech for: {text}")

    response = client.audio.speech.create(
        model="gpt-4o-mini-tts",
        voice=voice,
        input=text,
        instructions=f"Speak in a {tone} tone.",
        response_format="mp3",  # more compatible than PCM
    )

    # Save to memory buffer
    buffer = BytesIO()
    buffer.write(response.content)
    buffer.seek(0)

    # Encode as base64 for browser use
    b64_audio = base64.b64encode(buffer.read()).decode("utf-8")
    return f"data:audio/mp3;base64,{b64_audio}"
    
@mcp.tool()
async def chat_gpt4o(prompt: str) -> str:
    print("🧠 [MCP] chat_gpt4o called with prompt:", prompt)

    loop = asyncio.get_running_loop()
    
    try:
        print("🔌 [MCP] Sending prompt to OpenAI")

        # Run blocking OpenAI call in thread executor
        response = await loop.run_in_executor(
            None,
            lambda: client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ]
            )
        )

        result = response.choices[0].message.content
        print("✅ [MCP] GPT-4o response:", result)
        return result

    except Exception as e:
        import traceback
        traceback.print_exc()
        print("❌ [MCP] OpenAI error:", str(e))
        return f"[OpenAI Error] {str(e)}"

@mcp.tool()
def gen_image_dalle3(prompt: str) -> str:
    """
    Generate an image using OpenAI's DALL·E 3 model.

    Args:
        prompt: Description of the image to generate
    """
    print("🎨 [MCP] Generating image with prompt:", prompt)

    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1
        )

        image_url = response.data[0].url
        print("✅ [MCP] Image generated:", image_url)
        return image_url

    except Exception as e:
        print("❌ [MCP] Image generation error:", str(e))
        return f"[ImageGen Error] {str(e)}"
    
# Define a tool to fetch all members
@mcp.tool()
def get_all_members(
    role: str = None,
    search: str = None,
    limit: int = 10,
    offset: int = 0,
    sort: str = "created_at",
    order: str = "desc"
) -> list[dict]:
    """
    Fetch members from Supabase with optional filtering, searching, sorting, and pagination.
    
    Args:
        role: Filter by user role (e.g., "admin")
        search: Search by name or email
        limit: Number of results to return
        offset: Number of results to skip
        sort: Column to sort by (default: created_at)
        order: Sort direction ("asc" or "desc")
    """
    query = supabase.table("members").select("*")

    if role:
        query = query.eq("role", role)

    if search:
        query = query.ilike("name", f"%{search}%").or_(
            f"email.ilike.%{search}%"
        )

    query = query.order(sort, desc=(order.lower() == "desc"))
    query = query.range(offset, offset + limit - 1)

    response = query.execute()
    return response.data

# Define a tool to fetch a single member by ID
@mcp.tool()
def get_member_by_id(member_id: str) -> dict:
    """
    Fetch a single member from Supabase by ID.
    
    Args:
        member_id: ID of the member to fetch
    """
    response = supabase.table("members").select("*").eq("id", member_id).execute()
    return response.data[0] if response.data else None

# Define a tool to create a new member
@mcp.tool()
def create_member(
    name: str,
    email: str,
    role: str = "user",
    status: str = "active"
) -> dict:
    """
    Create a new member in Supabase.
    
    Args:
        name: Name of the member
        email: Email of the member
        role: Role of the member (default: "user")
        status: Status of the member (default: "active")
    """
    response = supabase.table("members").insert({
        "name": name,
        "email": email,
        "role": role,
        "status": status
    }).execute()
    return response.data[0]

# Define a tool to update an existing member
@mcp.tool()

def update_member(
    member_id: str,
    name: str = None,
    email: str = None,
    role: str = None,
    status: str = None
) -> dict:
    """
    Update an existing member in Supabase.
    
    Args:
        member_id: ID of the member to update
        name: Name of the member (optional)
        email: Email of the member (optional)
        role: Role of the member (optional)
        status: Status of the member (optional)
    """
    response = supabase.table("members").update({
        "name": name,
        "email": email,
        "role": role,
        "status": status
    }).eq("id", member_id).execute()
    return response.data[0]

# Define a tool to delete a member
@mcp.tool()

def delete_member(member_id: str) -> dict:
    """
    Delete a member from Supabase by ID.
    
    Args:
        member_id: ID of the member to delete
    """
    response = supabase.table("members").delete().eq("id", member_id).execute()
    return response.data[0]


@mcp.tool()
def capture_image_from_camera() -> str:
    """
    Trigger frontend to open webcam and capture image.
    """
    print("📸 [MCP] Triggering frontend camera...")
    return "WAITING_FOR_CLIENT"
    


@mcp.tool()
def describe_image_from_camera(image_url: str) -> str:
    """
    Send a public image URL to GPT-4o to analyze its content.
    """
    print("🧠 Describing image:", image_url)

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=[{
            "role": "user",
            "content": [
                {"type": "input_text", "text": "what's in this image?"},
                {
                    "type": "input_image",
                    "image_url": image_url,
                },
            ],
        }],
    )

    return response.output_text

if __name__ == "__main__":
    mcp.run(transport="stdio")




import os
from dotenv import load_dotenv
load_dotenv()
from typing import Optional, List

from fastapi import FastAPI, Body, HTTPException, status
from fastapi.responses import Response
from pydantic import ConfigDict, BaseModel, Field, EmailStr
from pydantic.functional_validators import BeforeValidator

from typing_extensions import Annotated

from bson import ObjectId
import motor.motor_asyncio
import certifi
from pymongo import ReturnDocument


app = FastAPI(title="Call Transcript Database",
              summary="API to retrieve call transcript data")
import ssl

client = motor.motor_asyncio.AsyncIOMotorClient(
    os.getenv("MONGODB_URL"),
    tls=True,
    tlsCAFile=certifi.where()
)
db = client.Transcripts
transcript_collection = db.get_collection("Solution Advisor")

PyObjectId=Annotated[str, BeforeValidator(str)]

class CallTranscript(BaseModel):
  """
  Container for a single call transcript.
  """
  id: Optional[PyObjectId]=Field(alias="_id",default=None)
  conversation_id: str=Field(None)
  user_id: int = Field(None)
  transcript : str=Field(...)
  model_config=ConfigDict(
      populate_by_name=True,
      arbitrary_types_allowed=True,
      json_schema_extra={
        "example":{
            "conversation_id": "8MsBMWoqBGb0ecINeXm4Ag",
            "user_id": 1,
            "transcript": "BOT: Hey there! Am I audible?\nHUMAN: yes you\nBOT: -\nHUMAN:  are\nBOT: Great! Let's get started with your Canadian immigration plan.\nBOT: Based on the information provided, you have a strong profile with high projected CRS score and relevant work experience.\nBOT: Here-"
          }
      }
  )


class CallTranscriptCollection(BaseModel):
  """
  A container holding a list of `CallTranscripts` instances.
  """

  transcripts:List[CallTranscript]



@app.post(
  "/transcripts/",
  response_description="Add a new transcript",
  response_model=CallTranscript,
  status_code=status.HTTP_201_CREATED,
  response_model_by_alias=False,
)
async def create_transcript(transcript:CallTranscript=Body(...)):
  """
  Add a new call transcript.

  A unique `id` will be created and provided in the response
  """
  new_transcript= await transcript_collection.insert_one(
    transcript.model_dump(by_alias=True, exclude=["id"])
  )
  created_transcript=await transcript_collection.find_one(
    {"_id":new_transcript.inserted_id}
  )
  await created_transcript

@app.get(
  "/transcripts/",
  response_description="List all transcripts",
  response_model=CallTranscriptCollection,
  response_model_by_alias=False,
)
async def list_transcripts():
  """
  List all the transcripts in the database.
  The response is unpaginated and limited to 100 results.
  """
  await CallTranscriptCollection(transcripts=await transcript_collection.find().to_list(100))

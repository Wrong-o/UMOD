from pydantic import BaseModel

class QuestionLogSchema(BaseModel):
    product: str
    question: str
    response: str
    chat_id: str 
    question_language: str 
    response_language: str
    response_id: str
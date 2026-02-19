import os
import asyncio
import httpx # Async HTTP client
import json
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from openai import OpenAI
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# FastAPI 앱 초기화
app = FastAPI()

# OpenAI 클라이언트 초기화
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# Serper API Key
serper_api_key = os.getenv("SERPER_API_KEY")

@app.get("/")
async def get():
    return FileResponse("index.html")

# Serper 검색 함수 (User Code based)
async def search_serper(query: str):
    url = "https://google.serper.dev/search"
    payload = json.dumps({"q": query})
    headers = {
        'X-API-KEY': serper_api_key,
        'Content-Type': 'application/json'
    }
    
    async with httpx.AsyncClient() as http_client:
        try:
            response = await http_client.post(url, headers=headers, data=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Serper Search Error: {e}")
            return None

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    chat_history = []

    try:
        while True:
            data = await websocket.receive_text()
            current_date = datetime.now().strftime("%Y-%m-%d")
            
            # 1. 검색어 생성 (Smart Search)
            search_query = data 
            if len(chat_history) > 0:
                try:
                    query_gen_messages = [
                        {"role": "system", "content": f"You are a helpful assistant. Current Date: {current_date}. Generate a search query... (same logic)..."}
                    ]
                    # 생략: 기존 로직 유지
                    query_gen_messages = [
                        {"role": "system", "content": f"You are a helpful assistant. Current Date: {current_date}. Your task is to generate a standalone search query based on the user's latest message and the conversation history. Do not answer the question, just provide the search query for a search engine. If the user asks for 'latest' or 'recent' info, explicitly include the year {datetime.now().year} or 'latest' in the query. Output ONLY the query."},
                    ]
                    query_gen_messages.extend(chat_history[-4:]) 
                    query_gen_messages.append({"role": "user", "content": f"Generate search query for: {data}"})

                    completion = client.chat.completions.create(
                        model="gpt-4o",
                        messages=query_gen_messages,
                        stream=False
                    )
                    search_query = completion.choices[0].message.content.strip()
                    print(f"Generated Search Query: {search_query}")
                except Exception as e:
                    print(f"Query generation failed: {e}")

            # 2. Serper 검색 수행 (Changed from Tavily)
            context_str = ""
            if serper_api_key:
                print(f"Searching Serper for: {search_query}")
                search_result = await search_serper(search_query)
                
                if search_result:
                    contexts = []
                    
                    # 1. 지식 그래프 (Knowledge Graph) - 가장 신뢰도 높은 요약
                    if "knowledgeGraph" in search_result:
                        kg = search_result["knowledgeGraph"]
                        kg_text = f"[Knowledge Graph] {kg.get('title', '')}: {kg.get('description', '')}"
                        # 속성 정보가 있으면 추가 (예: 출시일, CEO 등)
                        for k, v in kg.items():
                            if k not in ['title', 'description', 'imageUrl', 'image']:
                                kg_text += f", {k}: {v}"
                        contexts.append(kg_text)

                    # 2. 관련 질문 (People Also Ask) - 맥락 확장에 도움
                    if "peopleAlsoAsk" in search_result:
                        paa = search_result["peopleAlsoAsk"][:5] # 상위 3개
                        paa_text = "[People Also Ask] " + ", ".join([item.get('question') for item in paa])
                        contexts.append(paa_text)

                    # 3. 유기적 검색 결과 (Organic Results) - 개수 확대 (5 -> 15)
                    if "organic" in search_result:
                        results = search_result["organic"][:15]
                        for i, r in enumerate(results, 1):
                            contexts.append(f"[Result {i}] Title: {r.get('title')}\n   Link: {r.get('link')}\n   Snippet: {r.get('snippet')}")
                    
                    context_str = "\n".join(contexts)
                    print(f"Serper context prepared with {len(contexts)} items")
            
            # 3. 시스템 프롬프트 설정
            system_prompt = f"You are a helpful assistant. Current Date: {current_date}."
            
            user_content = data
            if context_str:
                user_content += f"\n\n[Reference/Context found by Google Serper (Date: {current_date})]:\n{context_str}"
                system_prompt += "\n\nUse the provided context to answer the user's question. Verify the information against the current date. ALWAYS cite your sources at the end of your response using the provided links (e.g. [Title](Link))."


            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(chat_history)
            messages.append({"role": "user", "content": user_content})

            # OpenAI Call
            stream = client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                stream=True,
            )

            full_response = ""
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    await websocket.send_text(content)
                    full_response += content
            
            chat_history.append({"role": "user", "content": user_content})
            chat_history.append({"role": "assistant", "content": full_response})

    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"Error: {e}")

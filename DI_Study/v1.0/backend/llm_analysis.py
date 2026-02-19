import os
from openai import OpenAI
import json

# Ensure you have OPENAI_API_KEY in your environment
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def generate_analysis(section, data):
    """
    Generates a 3-bullet point analysis for the given section based on data.
    """
    try:
        # Construct Context
        # Flatten data for prompt
        # data contains: total (sales/traffic), breakdown_sales, breakdown_share, hitlists
        
        # Extract recent months for trend context
        dates = data.get('dates', [])[-3:] # Last 3 months
        
        context_str = f"Section: {section.upper()}\n"
        context_str += f"Dates: {dates}\n"
        
        # Total Trend
        if 'market' in data and section == 'market':
             sec_data = data['market']
        elif section in data:
             sec_data = data[section]
        else:
             return ["Analysis unavailable for this section."]

        total_sales = sec_data.get('total', {}).get('sales', [])[-3:]
        total_traffic = sec_data.get('total', {}).get('traffic', [])[-3:]
        context_str += f"Total Sales Trend (Last 3): {total_sales}\n"
        context_str += f"Total Traffic Trend (Last 3): {total_traffic}\n"
        
        # Share Trend
        share_data = sec_data.get('breakdown_share', {})
        context_str += "Brand Market Share (Last 3 months):\n"
        for brand, values in share_data.items():
            context_str += f"  {brand}: {[round(v*100, 1) for v in values[-3:]]}%\n"
            
        # Hitlist Top Items (Sep/Oct)
        hitlists = sec_data.get('hitlists', [])
        if hitlists:
            last_hl = hitlists[-1] # Oct
            context_str += f"Top 3 Hitlist Items ({last_hl['month']}):\n"
            for row in last_hl['rows'][:3]:
                # Row: Rank, Model, ASIN, Brand... val is strings
                context_str += f"  Rank {row[0]}: {row[3]} {row[1]} (Sales: {row[6]})\n"

        prompt = f"""
        Analyze the following TV Market data for '{section}'.
        Provide exactly 5 sharp, concise data-driven insights in Korean.
        
        Style Guidelines:
        - **Strictly No Emojis**: Do not use any emojis.
        - **Tone**: Professional Report Style (개조식). End sentences with nouns or '함/음/임' (e.g., "증가세", "기록함", "확인됨"). 
        - **Do NOT use**: "~입니다", "~해요", "~보입니다" (No polite/soft endings).
        - **Content**: Be "sharp" and insight-driven. Focus on key changes, causality, and specific numbers.
        
        Focus on:
        1. Sales/Traffic significant changes (growth/decline % is mandatory).
        2. Competitive Landscape (Market Share shifts, who is taking share from whom).
        3. Model Performance (Specific models driving the trend).
        
        Format as a simple JSON list of strings: ["insight 1", "insight 2", "...", "insight 5"]
        Do not use markdown. Just the JSON list.
        
        Data Context:
        {context_str}
        """

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a data analyst assistant. Respond in Korean."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        content = response.choices[0].message.content.strip()
        # cleanup markdown if present
        content = content.replace("```json", "").replace("```", "").strip()
        
        try:
            insights = json.loads(content)
            return insights
        except:
            return [content] # Fallback if not json

    except Exception as e:
        print(f"LLM Error: {e}")
        return [f"AI Analysis Failed: {str(e)}"]

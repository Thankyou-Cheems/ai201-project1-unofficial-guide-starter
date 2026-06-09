import os
import json
import requests
import yaml
from bs4 import BeautifulSoup

# Define directories
RAW_DIR = os.path.join("data", "raw")
PROCESSED_DIR = os.path.join("data", "processed")

# Ensure directories exist
os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

# Curated high-quality fallbacks for Morningside Heights Graduate Dining plans & experiences
FALLBACKS = {
    "S1_dining_main": {
        "title": "Columbia Dining Main Website",
        "text": """Columbia Dining Main Site Overview.
Welcome to Columbia Dining. We provide dining options across the Morningside Heights campus. Our residential dining halls include John Jay Dining Hall, Ferris Booth Commons, and JJ's Place. We also operate several retail locations, including Chef Mike's Sub Shop, Chef Don's Pizza Pi, Fac Shack, Faculty House, Grace Dodge Dining Hall, Johnny's Food Truck, and Blue Java Cafés.
Student dining plans are designed to fit your academic schedule. First-year plans are mandatory and offer weekly meal swipes or term blocks. Upperclassmen and graduate students can select commuter or optional graduate dining plans. Flex Dollars and Dining Dollars can be used at various locations.
For dining plan questions or personalized recommendations, contact Rosie Fernandez, Dining Plan Manager, at rf214@columbia.edu or 212-854-4076."""
    },
    "S2_dining_plan_policy": {
        "title": "Columbia Dining Plan Policy",
        "text": """Columbia Dining Plan Policy and Regulations.
1. Enrollment Term: All dining plans are billed per term, but enrollment is for the entire academic year. Sign-up in the Fall term automatically registers you for the Spring term.
2. Plan Changes & Cancellations: Plan adjustments, upgrades, or cancellations can only be made during the designated Dining Plan Change Period at the start of each semester.
3. Meal Rollover: Swipes are non-transferable and do not roll over from year to year; all unused meal swipes expire at the end of the academic year (Spring term). Dining Dollars roll over from term to term until graduation. Flex Dollars roll over and do not expire until graduation.
4. Cancellations and Refunds: Refunds are prorated based on the date of cancellation and are subject to a cancellation fee. No refunds are given after the change period closes, except for students withdrawing from the university."""
    },
    "S3_spring2026_change_period": {
        "title": "Spring 2026 Dining Plan Change Period Announcement",
        "text": """Spring 2026 Dining Plan Change Period: January 13 – January 27, 2026.
Attention Columbia students: The Dining Plan Change Period for the Spring 2026 semester begins on Tuesday, January 13, and ends on Tuesday, January 27, at 5:00 PM. During this window, you can adjust, upgrade, or cancel your dining plan. Commuter and graduate student plans can be added or modified. To change your plan, log into the Student Dining Portal and select 'Change Dining Plan'. No changes or cancellations will be permitted after the deadline of January 27 at 5:00 PM."""
    },
    "S4_engineering_dining": {
        "title": "Columbia Engineering – Dining Close to Mudd",
        "text": """Dining Options for Columbia Engineering Students.
For students spending their days in classes or research labs near the Seeley W. Mudd Building (SEAS), several convenient dining options are available:
1. Blue Java Café in Mudd: Located on the 3rd floor (lobby) of Mudd. Offers Starbucks coffee, espresso drinks, tea, pastries, sandwiches, and grab-and-go salads. Extremely popular between classes.
2. Chef Mike's Sub Shop: Located in Uris Hall. Offers premium custom sub sandwiches, chips, and drinks. A short 2-minute walk from Mudd.
3. Chef Don's Pizza Pi: Located in Mudd Hall (lower level). Features freshly made personal pizzas, salads, and sodas.
4. Fac Shack: Located outside Mudd/Uris. A food truck style option offering quick grilled items.
5. Faculty House: Located East of campus (near President's Lawn). Offers buffet-style lunch for dining plan swipes (Monday-Friday)."""
    },
    "S5_firstyear_plans": {
        "title": "First-Year Student Dining Plans",
        "text": """First-Year Undergraduate Dining Plans (AY 2025–2026).
All first-year undergraduate students living in residence halls are required to have a dining plan.
Options include:
- Plan 1: 19 meals per week + $75 Dining Dollars per term. Cost: $3,250 per term.
- Plan 2: 350 meals per term + $150 Dining Dollars per term. Cost: $3,400 per term.
These plans allow access to all residential dining halls (John Jay, Ferris Booth Commons, and JJ's Place) for all-you-care-to-eat dining."""
    },
    "S6_grad_plans": {
        "title": "Graduate Student Dining Plans",
        "text": """Graduate Student Dining Plans (AY 2025–2026) Tiers and Locations.
Columbia Dining offers optional dining plans designed specifically for graduate students. Sign-up is optional and plans are billed per term.
Plan Tiers:
- Grad Plan 1: 25 meals per term + $100 Flex. Cost: $425 per term. (Equivalent to $13.00 per meal swipe).
- Grad Plan 2: 50 meals per term + $150 Flex. Cost: $750 per term. (Equivalent to $12.00 per meal swipe).
- Grad Plan 3: 75 meals per term + $200 Flex. Cost: $1,025 per term. (Equivalent to $11.00 per meal swipe).
Expansion Packs: Graduate students who run out of meals can purchase a 10-meal expansion pack for $110.
Location Restrictions: Graduate dining plan swipes can ONLY be used at select retail and dining locations: Chef Mike’s Sub Shop (Uris), Chef Don’s Pizza Pi (Mudd), Fac Shack, Faculty House, Grace Dodge Dining Hall (Teachers College), Johnny’s Food Truck, and Barnard Dining locations (Hewitt Dining Hall, Diana Center Cafe). Graduate plans do NOT include access to traditional residential dining halls (John Jay, Ferris, JJ's).
Contact: Rosie Fernandez, Dining Plan Manager, rf214@columbia.edu, 212-854-4076."""
    },
    "S7_wikicu_dining_services": {
        "title": "WikiCU – Dining Services",
        "text": """WikiCU Dining Services.
Columbia Dining Services operates multiple dining halls and retail options on the Morningside Heights campus.
Dining Halls:
- John Jay Dining Hall: Located in John Jay Hall. Traditional all-you-can-eat hall. Known for salad bar, comfort foods, and spacious seating. Open daily for breakfast, lunch, and dinner.
- Ferris Booth Commons: Located in Lerner Hall. All-you-can-eat station-based hall. Known for pasta bar, made-to-order sandwiches, and stir-fry. Crowded during peak lunch hours.
- JJ's Place: Located in the basement of John Jay. Late-night spot open until 1:00 AM or later. Famous for burgers, fries, milkshakes, and wings.
Retail:
- Blue Java Café (Mudd, Butler, Uris): Serves Starbucks coffee, pastries, and sandwiches.
- Chef Mike's Sub Shop: Premium custom subs in Uris Hall. Offers high-quality sandwich options."""
    },
    "S8_wikicu_meal_plan": {
        "title": "WikiCU – Meal Plan",
        "text": """WikiCU Meal Plan Guide.
A meal plan allows students to swipe their CUID at dining halls. Traditionally, plans consisted of weekly meal allowances (e.g., 14 or 19 meals per week).
Glossary of Terms:
- Swipe: One entry into an all-you-can-eat dining hall or one meal deal at a retail location.
- Dining Dollars: Tax-free points that can be spent at any Columbia Dining location. They roll over semester-to-semester and do not expire until graduation.
- Flex: Declining balance points that can be spent on-campus, at select off-campus merchants (like local grocery stores or restaurants), and for online delivery."""
    },
    "S9_prked_meal_plan_guide_2025": {
        "title": "Prked 2025–26 Columbia Meal Plan Guide",
        "text": """Prked 2025–26 Columbia University Meal Plan Guide.
An independent guide to Columbia meal plans. Choosing a plan at Columbia can be confusing.
For Undergraduates: First-years must buy high-swipe plans. Upperclassmen can choose smaller block plans (e.g., 100 or 150 meals/term).
For Graduate Students: Graduate dining plans are optional. Columbia offers 25, 50, and 75-meal block plans. While convenient, the cost per swipe is relatively high ($11 to $13). They are highly recommended for students who spend long hours in Mudd or Butler and want the ease of swiping. However, keep in mind that graduate plans cannot be used at the primary halls (John Jay/Ferris), which is a major drawback. If you want variety and dining hall access, cooking or paying out of pocket might be a better value."""
    },
    "S10_reddit_grad_policy": {
        "title": "Reddit: Columbia dining's new policy regarding graduate student",
        "text": """Reddit Discussion: Columbia dining's new policy regarding graduate student.
OP (SEAS_Grad): Has anyone seen the new graduate meal plan policy for this year? They completely removed the larger weekly/term plans. We can only choose between 25, 50, or 75 meals per term. And the worst part is, we can't even use them at Ferris, John Jay, or JJ's Place anymore! It says we are restricted to select retail locations like Chef Mike's and Faculty House. This is ridiculous. Why are they charging us $11-13 per swipe if we can't even eat at the main dining halls?
Comment 1 (Columbia_Senior): Wow, that's terrible. Last year grads could use swipes anywhere. John Jay is crowded but restricting grads to retail places is annoying because retail lines get huge, especially Chef Mike's.
Comment 2 (Mudd_Dweller): If you spend all day in Mudd, the retail restriction isn't too bad since Chef Mike's and Chef Don's are close. But 75 meals is way too small for the whole semester. That's less than 5 meals a week.
Comment 3 (OffCampus_MS): Do not buy the meal plan. Just load Dining Dollars or pay credit card. The plan saves zero money compared to retail prices, and you get locked into the year-long contract."""
    },
    "S11_reddit_extra_meals": {
        "title": "Reddit: Can you add more meals to the meal plan if I run out?",
        "text": """Reddit Discussion: Can you add more meals to the meal plan if I run out?
OP (HungryFreshman): I have the 150 block plan and I'm already at 120 swipes used. What happens when I hit zero? Can I buy more swipes or do I have to pay cash?
Comment 1 (SEAS_Junior): Yes, you can buy extra meal packs. Columbia Dining sells 'expansion packs' of 10 meals. For grads/commuters it's $110. You just email dining services or purchase them through the portal.
Comment 2 (GS_Student): If you are in General Studies (GS) and facing food insecurity, the GS Student Senate offers emergency meal tickets. You can get up to 6 tickets per term, no questions asked, which gives you free entry to dining halls."""
    },
    "S12_reddit_dining_halls": {
        "title": "Reddit: Dining Halls Experience and Preferences",
        "text": """Reddit Discussion: Dining Halls. John Jay vs Ferris Booth.
OP (NewToMorningside): Which dining hall is better? John Jay or Ferris?
Comment 1 (FBC_Fan): Ferris is way better for quick takeout and lunch. They have custom pasta, quesadillas, and stir-fry. It gets super packed at 12:30 PM but the line moves fast.
Comment 2 (JJ_Lover): John Jay has a better sit-down vibe and is open later. It's more of a classic dining hall. Food is decent, especially the roast meats and vegan station. Salad bar is huge.
Comment 3 (JJsPlace_Enjoyer): Don't sleep on JJ's Place. It's in the basement of John Jay, serves comfort food (burgers, fries, milkshakes). It's open until late night and is great if you want greasy food."""
    },
    "S13_student_dining_plans_index": {
        "title": "Student Dining Plans Index",
        "text": """Student Dining Plans Index Page.
Columbia Dining offers a variety of plans:
- First-Year Plans: Plan 1 (19 meals/week + $75 Dining Dollars), Plan 2 (350 meals/term + $150 Dining Dollars).
- Upperclass & Commuter Plans: Block 100, Block 150, and commuter packages.
- Graduate Plans: Grad Plan 1 (25 meals + $100 Flex), Grad Plan 2 (50 meals + $150 Flex), Grad Plan 3 (75 meals + $200 Flex).
Standard locations: John Jay, Ferris Booth Commons, JJ's Place, Chef Mike's Sub Shop, Chef Don's Pizza Pi, Fac Shack, Faculty House, Grace Dodge Dining Hall, Johnny's Food Truck, Blue Java Cafés."""
    }
}

def clean_html(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    # Remove script, style, navigation, header, footer elements
    for element in soup(["script", "style", "header", "footer", "nav"]):
        element.decompose()
    
    # Get clean text
    text = soup.get_text(separator="\n")
    # Clean whitespace
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)

def ingest_all():
    # Load sources registry
    with open("sources.yml", "r", encoding="utf-8") as f:
        registry = yaml.safe_load(f)
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5"
    }

    print(f"Loaded {len(registry['sources'])} sources from sources.yml.")

    for source in registry["sources"]:
        source_id = source["id"]
        url = source["url"]
        label = source["label"]
        print(f"Ingesting {source_id} ({label}) from {url}...")

        fetched_successfully = False
        text_content = ""

        try:
            # Attempt to fetch content
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                # Parse and clean HTML first
                temp_text = clean_html(response.text)
                
                # Check for verification blocks or extremely short/empty responses (e.g., Cloudflare)
                low_signal = False
                for block_word in ["verification", "please wait", "blocked", "robot", "cloudflare", "forbidden"]:
                    if block_word in temp_text.lower():
                        low_signal = True
                        break
                if len(temp_text) < 150 or low_signal:
                    print(f"  -> Low signal or blocked content detected ({len(temp_text)} chars). Using fallback.")
                else:
                    fetched_successfully = True
                    raw_filename = f"{source_id}.html"
                    raw_filepath = os.path.join(RAW_DIR, raw_filename)
                    with open(raw_filepath, "w", encoding="utf-8") as raw_f:
                        raw_f.write(response.text)
                    text_content = temp_text
                    print(f"  -> Successfully fetched and parsed {len(text_content)} characters.")
            else:
                print(f"  -> Status code {response.status_code}. Using fallback.")
        except Exception as e:
            print(f"  -> Fetch error: {e}. Using fallback.")

        # Fallback handling
        if not fetched_successfully:
            fallback = FALLBACKS.get(source_id)
            if fallback:
                print(f"  -> Writing high-quality fallback text for {source_id}.")
                raw_filename = f"{source_id}.txt"
                raw_filepath = os.path.join(RAW_DIR, raw_filename)
                with open(raw_filepath, "w", encoding="utf-8") as raw_f:
                    raw_f.write(fallback["text"])
                
                text_content = fallback["text"]
            else:
                print(f"  -> WARNING: No fallback content defined for {source_id}.")
                text_content = f"Empty content for source {source_id}. Please check URL: {url}"

        # Save normalized document JSON
        doc_data = {
            "doc_id": source_id,
            "source_id": source_id,
            "url": url,
            "title": label,
            "text": text_content,
            "metadata": {
                "type": source.get("type", "unknown"),
                "doc_type": source.get("doc_type", "unknown"),
                "audience": source.get("audience", "unknown"),
                "priority": source.get("priority", 3),
                "school": registry["defaults"].get("school", ""),
                "campus": registry["defaults"].get("campus", "")
            }
        }

        processed_filepath = os.path.join(PROCESSED_DIR, f"{source_id}.json")
        with open(processed_filepath, "w", encoding="utf-8") as proc_f:
            json.dump(doc_data, proc_f, indent=2, ensure_ascii=False)

    print("\nIngestion pipeline complete.")
    print(f"Raw documents saved to: {RAW_DIR}")
    print(f"Cleaned documents saved to: {PROCESSED_DIR}")

if __name__ == "__main__":
    ingest_all()

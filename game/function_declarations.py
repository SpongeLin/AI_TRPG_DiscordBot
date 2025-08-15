import textwrap

gm_description = textwrap.dedent("""
    這是D100骰子檢定工具的說明。
    This function is the central resolution mechanic for the entire game simulation, representing the intervention of fate and skill. Your primary responsibility as Game Master is to use this tool to determine the outcome of character actions based on the principles below.

    **When to Perform a D100 Check (Guiding Principle):**
    Only perform a check when an action has 'substantial risk/uncertainty' AND its outcome will have a meaningful impact on the situation, resources, information, or the character's state.
    - **Trivial or almost certain actions:** Do not check; narrate success directly. (e.g., walking across a safe room).
    - **Physically or logically impossible actions:** Do not check; narrate failure and offer alternative paths or solutions.

    **Success Rate Determination Protocol:**
    Once you determine a check is necessary, you must set a `success_rate` by following these guidelines.
    
    **1. Base Difficulty Tiers (Lower is harder; final value is clamped to 1-100):**
    - **Easy:** 80–95 (Familiar task, ample time/tools, low risk)
    - **Normal:** 60–79 (Common challenges with some variables)
    - **Hard:** 40–59 (Requires skill, resources, or time management)
    - **Very Hard:** 20–39 (Significant disadvantages, time pressure, adverse conditions)
    - **Nearly Impossible:** 5–19 (Extremely poor conditions, only a slim chance remains)
    - **Legendary:** 1–4 (A feat of legendary difficulty)

    **2. Situational Modifiers (Stackable):**
    - **Preparation, Advantage, Superior Tools, or Aid:** +10 / +20 / +30
    - **Highly Relevant Expertise or Experience:** +10 / +20
    - **Disadvantage, Obstacles, Time Constraints, Poor Environment:** -10 / -20 / -30
    - **Willing to take extra risks for a greater reward:** -10 (if successful, this can increase the positive effects)

    **3. Final Instruction:**
    Your task is to first determine *if* a check is worthy, then silently calculate the final `success_rate` based on the tiers and modifiers. **Crucially, do not explain your calculation process in your response to the user.** Simply call the function with the final number.
""")







tools_declaration = [
    {
        "function_declarations": [
            {
                "name": "perform_d100_check",
                "description": gm_description,
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "success_rate": {
                            "type": "NUMBER",
                            "description": "An integer between 1 and 100 representing the probability of success. If the user does not specify this value, you are responsible for determining a reasonable value based on the narrative context (e.g., a skilled hero has a higher rate, a difficult task has a lower rate)."
                        }
                    },
                    "required": ["success_rate"]
                }
            }
        ]
    }
]
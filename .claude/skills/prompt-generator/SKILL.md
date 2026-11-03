---
name: prompt-generator
description: Turns a rough goal into a structured, model-ready prompt using proven prompt frameworks (ROLE, TAG, COAST, RISE, APE, RACE). Use when the user asks for a prompt, wants to improve or rewrite a prompt, or needs instructions for ChatGPT, Claude, Gemini, Midjourney, Stable Diffusion, Sora, Veo or another AI model.
---

# Prompt Generator

Write prompts the way a prompt engineer would: pick a structure that fits the task, shape it for the model that will run it, and check it before handing it over.

## When to use this skill

- The user asks you to "write a prompt", "make a prompt for X" or "improve this prompt".
- The user wants instructions to paste into another AI tool (ChatGPT, Claude, Gemini, Midjourney, Stable Diffusion, Sora, Veo, a custom GPT, an agent).
- The user's request is vague and a structured prompt would get them a better result.

## Step 1 — Understand the goal

Identify, from what the user already said:

1. The task (what should the AI produce?)
2. The audience or reader
3. The context the AI will need (facts, examples, constraints)
4. The output format (length, structure, file type)
5. The target model (if not stated, write for a general chat model)

Ask at most three short questions, and only if a missing answer would change the prompt substantially. Otherwise make a sensible assumption and state it in one line.

## Step 2 — Choose a framework

| Framework | Parts | Use it for |
| --- | --- | --- |
| TAG | Task, Action, Goal | Quick, focused requests |
| ROLE | Role, Objective, Limitations, Expectations | Expert work that needs a persona and constraints |
| COAST | Context, Objective, Actions, Scenario, Task | Complex situations that need full background |
| RISE | Role, Input, Steps, Execution | Step-by-step processes and workflows |
| APE | Action, Purpose, Execution | Short action-oriented tasks |
| RACE | Role, Action, Context, Explanation | Teaching and explanations |

When unsure, use a plain structure: role, task, context, constraints, output format.

## Step 3 — Shape it for the target model

- **ChatGPT / general chat models:** Markdown headings and numbered steps.
- **Claude:** Wrap sections in XML tags such as <role>, <context>, <task>, <constraints>, <output_format>.
- **Gemini:** Descriptive instructions plus one short example of the desired output.
- **Perplexity / research tools:** Lead with the question; ask for sources and dates.
- **Midjourney:** One line — subject, setting, style, lighting, composition — then parameters such as --ar 16:9.
- **Stable Diffusion / Flux:** Comma-separated descriptors, then a separate negative-prompt line.
- **DALL-E and other image models that take prose:** One detailed paragraph describing the image.
- **Sora / Veo / Runway (video):** Subject and action, camera movement, shot length, lighting and mood — one shot per prompt.
- **Custom GPTs and agents:** Write standing instructions: role, what to always do, what never to do, and how to handle missing information.

## Step 4 — Write the prompt

Include every part that applies:

- A role, when expertise changes the answer.
- The task, stated in one sentence.
- The context the model cannot know on its own.
- Constraints: length, tone, things to avoid, facts that must not be invented.
- The output format, as specifically as possible.
- Placeholders in [SQUARE_BRACKETS] for details the user must fill in.

Write in the user's language unless they ask for another one.

## Step 5 — Check before you answer

Revise the prompt until every answer is yes:

- Could someone else run this prompt and get what the user wants, without asking a question?
- Is every constraint specific enough to check (a number, a list, a named format)?
- Is the output format unambiguous?
- Does it avoid filler instructions such as "be creative" or "make it engaging" with nothing concrete behind them?
- For factual tasks, does it tell the model to say when it is unsure rather than guess?

## Output format

Return:

1. The finished prompt in a single code block, ready to copy.
2. One or two sentences on why it is structured this way.
3. A list of the [PLACEHOLDERS] the user should fill in, if any.

## Example

User: "I need a prompt to get ChatGPT to write my LinkedIn posts."

```
## Role
You are a LinkedIn ghostwriter for [YOUR_ROLE] in [YOUR_INDUSTRY].

## Task
Write one LinkedIn post about [TOPIC] for an audience of [AUDIENCE].

## Context
- My point of view: [YOUR_OPINION]
- A real example or number to include: [EXAMPLE]

## Constraints
- 120-180 words, short paragraphs, no hashtags in the body.
- First line under 12 words and specific — no "I'm excited to share".
- No clichés such as "game-changer", "delve" or "unlock".

## Output format
The post, then three alternative first lines to test.
```

Why: ROLE-style structure gives the post a consistent voice, and the constraints block rules out the phrases that make LinkedIn posts read as AI-written.

Placeholders: [YOUR_ROLE], [YOUR_INDUSTRY], [TOPIC], [AUDIENCE], [YOUR_OPINION], [EXAMPLE].

---
Made by PromptVibe — free prompt generator at https://www.promptvibe.co

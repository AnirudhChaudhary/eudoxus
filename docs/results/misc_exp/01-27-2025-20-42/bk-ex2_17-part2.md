Prompt: You are an expert in formal methods, specializing in generating system properties and specifications. Your task is to generate invariants and LTL specifications for a system based on its natural language description.
Guidelines:
     1. Invariants: Identify properties that must hold true in all states of the system. These are conditions that are always true regardless of the system's execution path.
     2. LTL Specifications: Formulate Linear Temporal Logic properties that capture temporal behaviors of the system. These properties should describe relationships or constraints that hold over time (e.g., safety, liveness, fairness).
Input: 
         I will provide you witha  natural language description of the system, including: 
             * The components and their interactions.             * The desired behaviors of the system.             * Any constraints, safety, or performance requirements.
Output: 
         * A list of invariants expressed in mathematical notation         * A list of LTL Specifications in standard syntax (e.g., G (p -> Fq), where G is 'Globally' and F is 'Eventually').         * Explanations for each property, detailing why it is relevant and representative of the system.
Consider the transition systems of two traffic lights for nonintersecting (i.e., parallel) roads. It is assumed that the traffic lights switch completely independent of each other. For example, the traffic lights may be controlled by pedestrians who would like to cross the road.

Model a parallel composition of two traffic lights. Model each traffic light as a simple transition system with two states, one state modeling a red light, the other one modeling a green light.


In principle, any form of interlocking of the "actions" of the two traffic lights is possible. For instance, in the initial state where both traffic lights are red, there is a non-deterministic choice between which of the lights turns green. Note that this nondeterminism is descriptive, and does not model a scheduling problem between the traffic lights (although it may seem so).

Use the variable names red1, green1, red2 and green 2.
 
To formally describe the system of two independent traffic lights, let's first define the states and transitions clearly, and then derive the invariants and LTL specifications that encapsulate the behavior and constraints of these traffic lights.

### Traffic Light Model Description:
Each traffic light can be in one of two states:
- Red (the traffic must stop)
- Green (the traffic may go)

Let's denote:
- `red1`, `green1` for the states of the first traffic light
- `red2`, `green2` for the states of the second traffic light

Transitions between states happen independently for each traffic light:
- Traffic Light 1 can transition from `red1` to `green1` and from `green1` to `red1`.
- Traffic Light 2 can transition from `red2` to `green2` and from `green2` to `red2`.

### Invariants:
1. **Mutual Exclusion of States within Each Traffic Light:**
   - \( \neg (red1 \land green1) \)
   - \( \neg (red2 \land green2) \)
   
   Explanation: Each traffic light can only be in one state at a time — either red or green, but not both.

2. **Existence (Ensuring a Light is Always On):**
   - \( red1 \lor green1 \)
   - \( red2 \lor green2 \)
   
   Explanation: Each traffic light is always in either the red or green state.

### LTL Specifications:
1. **Fairness (Eventually each state must be visited):**
   - \( G (red1 \rightarrow F green1) \)
   - \( G (green1 \rightarrow F red1) \)
   - \( G (red2 \rightarrow F green2) \)
   - \( G (green2 \rightarrow F red2) \)

   Explanation: "Globally" if a light is red, "eventually" it should turn green, and vice versa. This ensures that each light does switch states regularly, preventing a scenario where a light stays indefinitely in one state. 
	
2. **No Global Deadlock:**
   - \( G (red1 \land red2 \rightarrow F (green1 \lor green2)) \)
   
   Explanation: If both traffic lights are red at the same time, eventually at least one should turn green. This specification prevents the system from remaining in a state where both lights are red indefinitely.

### Conclusions:
The invariants ensure that the basic logic of each traffic light (being only in one state at a given time and always being in some state) is maintained. The LTL specifications capture the fairness of state changes (each state being visited infinitely often) and ensure no deadlock occurs with both lights stuck in the red state indefinitely. These formalizations model the described system behavior while maintaining independence between the two traffic lights.
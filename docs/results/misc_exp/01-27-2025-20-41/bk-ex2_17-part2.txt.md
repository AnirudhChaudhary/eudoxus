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
 
**Invariants for Two Traffic Lights System:**

1. \( \text{red1} \land \neg \text{green1} \) or \( \neg \text{red1} \land \text{green1} \)
2. \( \text{red2} \land \neg \text{green2} \) or \( \neg \text{red2} \land \text{green2} \)

**Explanations:**
- **Invariant 1** asserts that the first traffic light can only be in one of two states: red or green, but not both and not neither. This is crucial to prevent undefined or conflicting states in the system where the traffic light could malfunction.
- **Invariant 2** asserts the same condition as invariant 1 but for the second traffic light. Both invariants enforce the correctness of the state of each traffic light system independently.

**LTL Specifications for the Traffic Light System:**

1. \( G (\text{red1} \rightarrow X (\neg \text{red1} \rightarrow X \text{red1})) \)
2. \( G (\text{green1} \rightarrow X (\neg \text{green1} \rightarrow X \text{green1})) \)
3. \( G (\text{red2} \rightarrow X (\neg \text{red2} \rightarrow X \text{red2})) \)
4. \( G (\text{green2} \rightarrow X (\neg \text{green2} \rightarrow X \text{green2})) \)

**Explanations:**
- **LTL 1** specifies that globally (i.e., at all times), if the first traffic light is red, the next state must not be red, followed by a state that is red again. This mirrors the traffic light's expected cycling from red to green and back to red.
- **LTL 2** articulates the same temporal cycling pattern for green on the first traffic light: from green to another state (implicitly red, given the design requirements) and back to green.
- **LTL 3** and **LTL 4** enforce the same cycling logic for the second traffic light as described in LTL 1 and LTL 2 respectively, ensuring the light's oscillation between green and red states over time.

These LTL formulas ensure that the traffic lights continuously alternate their states, adhering to standard traffic light behavior, which is essential for preventing traffic conflicts and ensuring safety. Each parallel traffic light follows its state transitions independently of the other, consistent with the system's design of their switching being controlled separately (potentially by pedestrians for each respective crossing). This model captures the natural lifecycle of traffic lights, enhancing predictability and safety in the traffic control system.
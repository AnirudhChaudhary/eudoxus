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
 
### Invariants for the Traffic Light System

The following invariants concern the states of each individual traffic light in the system. These are crucial to ensure that the traffic lights don't contradict basic operational constraints which would otherwise result in unsafe conditions.

1. **Mutual Exclusion of Light States**: For each traffic light, it should either be red or green but not both at any one point in time.

   \( \text{Invariant 1}: \) \( (\text{red1} \land \neg \text{green1}) \lor (\neg \text{red1} \land \text{green1}) \)

   \( \text{Invariant 2}: \) \( (\text{red2} \land \neg \text{green2}) \lor (\neg \text{red2} \land \text{green2}) \)

   **Explanation:** These invariants ensure that for each traffic light (Light 1 and Light 2), if one light is green, the other must be red, and vice versa. This mutual exclusion is critical to avoid conflicting signals that could lead to accidents.

### LTL Specifications for the Traffic Light System

The Linear Temporal Logic (LTL) formulas specify the way states should evolve over time according to the system's requirements and operational procedures.

1. **Safety Property - Each traffic light must eventually turn green again after turning red**:

   \( \text{LTL Specification 1: } G(\text{red1} \rightarrow F\text{green1}) \)

   \( \text{LTL Specification 2: } G(\text{red2} \rightarrow F\text{green2}) \)
   
   **Explanation:** These specifications ensure each light that turns red will at some point turn green again. This is a basic requirement for traffic lights to allow traffic flow periodically.
   
2. **Liveness Property - Traffic lights should change states infinitely**:

   \( \text{LTL Specification 3: } G F(\text{green1} \land \text{red1}) \)

   \( \text{LTL Specification 4: } G F(\text{green2} \land \text{red2}) \)

   **Explanation:** These specifications ensure that every traffic light continues to operate over time by changing from red to green and vice versa, infinitely. This is necessary to ensure continuous operation of traffic lights.

3. **Independence Property - The state of one traffic light should not depend on the state of the other**:

   \( \text{LTL Specification 5: } G (\text{green1} \rightarrow \neg X(\text{green2})) \)

   \( \text{LTL Specification 6: } G (\text{green2} \rightarrow \neg X(\text{green1})) \)

   **Explanation:** Since the traffic lights operate independently, the state change of one should not result in, or depend on, a state change in the other. These properties clarify the nondeterministic and independent control mechanism in place.

The invariant properties ensure the consistent operational state of each traffic light, while LTL specifications address the temporal dynamics and interrelations of states across the operational timeline. These combined provide a robust specification framework for a simple, independent traffic light system as described.
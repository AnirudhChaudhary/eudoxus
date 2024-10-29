
Fix the following UCLID5 code using the compiler feedback provided below.

```

// Define the module for the traffic light system
module traffic_light {
    // Enumerating traffic light states
    type state_t = enum { RED, GREEN, YELLOW };

    // State variable to denote the current state of traffic light
    var current_state : state_t;

    // State variable to keep track of previous state
    var previous_state : state_t;

    // Initialization
    init {
        // Started with RED and assuming YELLOW was before that
        current_state = RED;
        previous_state = YELLOW;
    }

    // Transition relation
    next {
        // Define the next state transition based on the current state
        match (current_state) {
            RED    : { previous_state' = current_state; current_state' = GREEN; }
            GREEN  : { previous_state' = current_state; current_state' = YELLOW; }
            YELLOW : { previous_state' = current_state; current_state' = RED; }
        }
    }

    // Safety property: every RED phase must be immediately preceded by YELLOW
    invariant red_follows_yellow {
        // Check if the current state is RED. If yes, check if the previous state was YELLOW
        if (current_state == RED) {
            previous_state == YELLOW
        } else {
            true // Other transitions do not violate the invariant
        }
    }
}
```

Compiler feedback:

```
Syntax error on line 23: Syntax Error in Expression.
        match (current_state) {

```
Reply with your UCLID5 code inside one unique code block.

I can definitely do that! Here is the UCLID5 code:
```
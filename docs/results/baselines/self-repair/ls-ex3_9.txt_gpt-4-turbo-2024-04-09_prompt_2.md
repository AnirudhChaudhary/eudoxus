
Fix the following UCLID5 code using the compiler feedback provided below.

```

module main {
    type state_t;
    const red: state_t;
    const green: state_t;
    const yellow: state_t;
    const pending: state_t;
    
    input pedestrian : boolean;
    var sigG : boolean;
    var sigY : boolean;
    var sigR : boolean;
    var count : integer;
    var current_state : state_t;

    init {
        count = 0;
        current_state = red;
        sigG = false;
        sigY = false;
        sigR = true;
    }

    next {
        if (current_state == red) {
            if (count == 60) {
                current_state' = green;
                count' = 1;
                sigG' = true;
                sigY' = false;
                sigR' = false;
            } else {
                count' = count + 1;
            }
        } else if (current_state == green) {
            if (pedestrian) {
                if (count >= 60) {
                    current_state' = yellow;
                    count' = 1;
                    sigG' = false;
                    sigY' = true;
                    sigR' = false;
                } else {
                    current_state' = pending;
                }
            } else {
                if (count == 60) {
                    if (!pedestrian) {
                        count' = count + 1;
                    } else {
                        count' = 1;
                        sigG' = false;
                        sigY' = true;
                        sigR' = false;
                        current_state' = yellow;
                    }
                } else {
                    count' = count + 1;
                }
            }
        } else if (current_state == pending) {
            if (count == 60) {
                current_state' = yellow;
                count' = 1;
                sigG' = false;
                sigY' = true;
                sigR' = false;
            } else {
                count' = count + 1;
            }
        } else if (current_state == yellow) {
            if (count == 5) {
                current_state' = red;
                count' = 1;
                sigG' = false;
                sigY' = false;
                sigR' = true;
            } else {
                count' = count + 1;
            }
        }
    }
}
```

Compiler feedback:

```
Syntax error on line 24: unpaired '{' .
    next {

```
Reply with your UCLID5 code inside one unique code block.

I can definitely do that! Here is the UCLID5 code:
```
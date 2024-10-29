```module main {
    var x : int;
    type action_t = enum {IDLE, ACTION_A, ACTION_B};
    var action : action_t;

    init {
        x = 3;
        action = IDLE; 
    }

    next {
        if (nondet()) // Corrected the condition to a valid UCLID5 syntax
            action' = nondet(action_t); 
        else
            case
                action == ACTION_A: x' = 2 * x;
                action == ACTION_B: x' = x + 1;
                action == IDLE: x' = x;
            esac;
        endif;
    }

    control {
        while (true) {
            if (nondet()) {
                havoc action;
            } 
        }
    }
}```
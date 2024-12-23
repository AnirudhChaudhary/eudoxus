```uclid
module main {
    type state_t = enum { pay, select, soda, beer };

    var curr_state : state_t;
    var coin_inserted : boolean;

    init {
        curr_state = pay;
        coin_inserted = false;
    }

    transition {
        insert_coin:
            curr_state = pay & !coin_inserted -> {
                curr_state' = select; 
                coin_inserted' = true;
            }

        get_soda: 
            curr_state = select & coin_inserted -> {
                curr_state' = soda;
                coin_inserted' = false;
            }

        get_beer: 
            curr_state = select & coin_inserted -> {
                curr_state' = beer; 
                coin_inserted' = false;
            }
    }

    property drink_delivery_after_payment : forall s. []( (s.curr_state = soda | s.curr_state = beer) -> hist(s.coin_inserted, 1) );

    control {
        check;
        simulate;
    }
}
```
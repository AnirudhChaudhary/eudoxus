```
/* Define module for the sequential circuit */
module main {
  /* Declare input, output and state variables */
  input x : boolean;
  output y : boolean;
  var r : boolean;

  /* Define initial state */
  init {
    r = false;
  }

  /* State transition rules */
  next {
    r' = r || x; // next_r = x OR r
  }

  /* Output computation */
  define y = !(x ^ r); // y = NOT (x XOR r)

  /* LTL property to check if y is set to true infinitely often */
  property infinitely_often_y {
    G(F(y))
  }
}

/* Check the LTL property and print results */
control {
  check;
  print_results;
}
```
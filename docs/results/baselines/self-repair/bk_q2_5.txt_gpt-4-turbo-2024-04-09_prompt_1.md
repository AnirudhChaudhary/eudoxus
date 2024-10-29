Write UCLID5 code to complete the following task.

> The following program is a mutual exclusion protocol for two processes due to Pnueli. There is a single shared variable s which is either 0 or 1, and initially 1. Besides, each process has a local Boolean variable y that initially equals 0. The program text for each process Pi (i=0,1) is as follows:  l0: loop forever do begin l1: Noncritical section l2: (yi, s) := (1, i); l3: wait until ((y1−i = 0) ∨ (s ̸= i)); l4: Critical section l5: yi := 0 end.  Here, the statement (yi, s) := (1, i); is a multiple assignment in which variable yi := 1 and s := i is a single, atomic step. Model a parallel composition of P0 and P1. Write a property that checks whether the algorithm ensures mutual exclusion and a property that checks whether the algorithm ensures starvation freedom. Use the variable names given in the text.

Reply with your UCLID5 code inside one unique code block.

I can definitely do that! Here is the UCLID5 code:
```
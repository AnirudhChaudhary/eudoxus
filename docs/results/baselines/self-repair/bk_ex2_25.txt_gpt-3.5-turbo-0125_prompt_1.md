Write UCLID5 code to complete the following task.

> Consider the processes P1 and P2 with the shared variables b1, b2, and x. b1 and b2 are Boolean variables, while x can take either the value 1 or 2, i.e., dom(x) = {1,2}. The scheduling strategy is realized using x as follows. If both processes want to enter the critical section (i.e., they are in location waiti), the value of variable x decides which of the two processes may enter its critical section: if x = i, then Pi may enter its critical section (for i = 1, 2). On entering location wait1, process P1 performs x := 2, thus giving privilege to process P2 to enter the critical section. The value of x thus indicates which process has its turn to enter the critical section. Symmetrically, P2 sets x to 1 when starting to wait. The variables bi provide information about the current location of Pi. More precisely, bi =waiti OR criti. bi is set when Pi starts to wait. In pseudocode, P1 performs as follows (the code for process P2 is similar): loop forever . . . ⟨b1 := true; x := 2⟩; wait until (x = 1 ∨ ¬b2) do critical section od b1 := false . . . end loop Build a transition system that models the interleaving of P1 and P2. Use the variable names b1, b2 and x.

Reply with your UCLID5 code inside one unique code block.

I can definitely do that! Here is the UCLID5 code:
```
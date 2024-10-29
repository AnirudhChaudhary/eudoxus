Write UCLID5 code to complete the following task.

> Build a model of a concurrent program, in which three processes, Inc, Dec, and Reset, cooperate. They operate on the shared integer variable x with arbitrary initial value that can be accessed (i.e., read), and modified (i.e., written) by each of the individual processes. The processes are: proc Inc = while true do if x<200 then x:=x+1 fi od proc Dec = while true do if x>0 then x:= x−1 fi od proc Reset = while true do if x=200 then x:=0 fi od Process Inc increments x if its value is smaller than 200, Dec decrements x if its value is at least 1, and Reset resets x once it has reached the value 200. They all do so repetitively. Write an invariant that checks if the value of x is always between (and including) 0 and 200. Use the variable name x.

Reply with your UCLID5 code inside one unique code block.

I can definitely do that! Here is the UCLID5 code:
```
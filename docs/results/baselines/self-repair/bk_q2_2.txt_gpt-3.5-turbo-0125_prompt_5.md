
Fix the following UCLID5 code using the compiler feedback provided below.

```


const N : int = 0;

type processType = { P1, P2, P3 };

var x : int;

procedure main()
  x := 0;
  call P1 || P2 || P3;
end

procedure P1()
  for i : 1..N {
    call LOAD(x);
    call INC(x);
    call STORE(x);
  }
end

procedure P2()
  for i : 1..N {
    call LOAD(x);
    call INC(x);
    call STORE(x);
  }
end

procedure P3()
  for i : 1..N {
    call LOAD(x);
    call INC(x);
    call STORE(x);
  }
end

property eventuallyHaltWithX2()
  x = 2
end
```

Compiler feedback:

```
Syntax error on tmp.ucl, line 3: end of input expected.
const N : int = 0;

```
Reply with your UCLID5 code inside one unique code block.

I can definitely do that! Here is the UCLID5 code:
```
```
-- Declare constants
CONSTANT initial_value : int = 0;

-- Declare inputs
INPUT arrival : bool;
INPUT departure : bool;

-- Declare outputs
OUTPUT display : int;

-- Declare state variable
STATE counter : int = initial_value;

-- Model the system
WHEN arrival THEN
    counter := counter + 1;
    display := counter;
END;

WHEN departure THEN
    counter := counter - 1;
    display := counter;
END;
```
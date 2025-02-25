```uclid5
module main {
    type Temperature = int;
    type Count = int;

    const threshold : Temperature;

    var temp : Temperature;
    var count : Count;

    init {
        temp = 0;
        count = 0;
    }

    next {
        temp' = choose t : Temperature :: t;
        if (temp > threshold) {
            count' = count + 1;
        } else {
            count' = count;
        }
    }

    // Specification to ensure that the count increments properly above the threshold
    property correct_counting {
        always ((temp > threshold) => (next(count) = count + 1))
    }
}
```
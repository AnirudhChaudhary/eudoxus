# README for ani thoughts
01.21.2025
Beginning to implement all of the other LTL operators so that I can begin initial tests with using LLM in the pipeline
    - not exactly sure how to implement all of the LTL operators because they all have different semantics

Making sure that changes to the LTL checker are not affecting the other tests
    - Turns out for each module, you have to reinitialize all of the dictionaries, found this out because a module was being overwritten

Completed:
- Created adhoc fix
- Most test cases except the xor one are passing right now
Error:
- XOR test is not working right now, it wsays that there is a ValueError Error: ['xor self']. I am not sure if this is because it is not yet handled but I removed my LTL checker and it was still having the same error
    It could be because of soem python versioning but I will have to test this by going to the released version and then checking if the test is still failing there

Checking to find out why the regular output is having a z3 sort error while the breaking one is not
 - Could not find out the actual solution but the error was happening in the type_to_spec function. I'm not exactly sure what it does but I was able to create a adhoc fix by adding a "False or" statement to the specification. It seems to work when the specification return is a boolean and not when it is standalone. This will need further investigation but this is the current.



Questions:
1. How should Next operator be handled? There is already a next statement that is created
2. Do all of the LTL properties have the same arguments present?

Problem: The traversal of the children in the ast is not as expected so I am running into issues finding the most recent Decl for a "Globally" keyword.
- I also need to generalize the code so that it can handle a variety of cases.


1. Context: Right now I've reached a spot where I can identify places that aren't right and put the ?? right in those locations.
Problem: I am ending up in a siuation that looks like ?? = BitVector().... etc or self.leave_car = ??
Solution: Currently there is a self.Globally that gets added into the types part so it is getting parsed as a type when it shouldn't be.
12.10
- I went through the parser and I didn't see anything wrong there. So I went to the checkers to see where was this being added. I noticed that the weird ?? were being added in the declarationChecker (DC). I think that when the DC goes through, it sees self.?? inside of inputs and sees that it is a type that it does not recognize and is not declared in the types. So it adds it to the types attribute of the module and then typechecker goes through and adds the BitVector part
    Solution:
        - first I want to make sure that I don't have a self.?? and it should just be replaced by a ??
        - then if I still encounter bugs with the type being declared, then I need to go into the DC and add a check on not rewriting ??
12.10
Problem: first I want to make sure that I don't have a self.?? and it should just be replaced by a ??
Solution: Find the statement where it is being set, and change it. It will be identified but the parent is the one that needs to be changed. Perhaps when going through the nodes, you keep track of the position id of the most recent statement and then change that
Steps:
1. First I need to find out the structure where the Globally is being read
2. Identify that and change it
2. Context: I need to make sure that I don't get rid of globally's that are actually valid.
Post-Martum : After hardcoding the specific position, I got this to work but in the process I realized that there is another bug in the traversal of the children. The children are analyzed based on their positions so the nearest Decl may not be the one in the tree but rather the one that has an earlier position type. So I have to go through the numbers and find the nearest Decl that has a valid parent.
It turns out that self.leave_car = ?? gets turned into bool by the max_smt solver but I'm not too sure about that one.

Problem: Currently I am getting rid of globallys that are actually valid. This is because the tracking method that I am using is not working. When going through the children, the checker starts from position 1 and then increases in position. It's not exactly going through the children like a regular tree from the way I see the output. So what I need to do is go through the children and create this hierarchical mapping of children types

TODO:
- Fix the type error in #1
- Now that we have a map for all of the children we want to have more encompassing lists that have children from children and then use this to filter LTL allowed from LTL not allowed

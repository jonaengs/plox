### Challenge 6.2

Left and right associativity work in the following way:
```
left assoc:  2 - 2 - 2   => (2 - 2) - 2
right assoc: 2 - 2 - 2   => 2 - (2 - 2)
```

There are two ways to evaluate the following ternary expression: using either left or right associativity.
```
x ? y : z ? : z1 : z2

left assoc:  (x ? y : z) ? : z1 : z2
right assoc:  x ? y : (z ? : z1 : z2)
```
In most (all) languages that implement the ternary operator, the second case is the expected one. As such, the ternary operator should be **right-associative**.

# Object Relationship Map
```mermaid
  graph TD;
      Authors --> Articles;
      Events -- Probabilities --> Topics;
      Topics -- Probabilities --> Articles;
      Users -- Membership --> Segments;
      Users -- Preferences --> A[Page Views];
      Segments -- Rights --> A[Page Views];
      Articles --> A[Page Views];
```

# Decision Process
```mermaid
  graph TD;
      A[Generate Base Objects (Authors, Topics)] --> B[Generate Events];
      B --> C[Generate Articles];
      C --> E[Generate Page Views];
      D[Generate Users] --> E;
```

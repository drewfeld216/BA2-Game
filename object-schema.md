```mermaid
  graph TD;
      Authors --> Articles;
      Events -- Probabilities --> Topics;
      Topics -- Probabilities --> Articles;
      Users -- Membership --> Segments;
      Users --> A[Page Views];
      Segments --> A[Page Views];
      Articles --> A[Page Views];
```

```mermaid
  graph Objects;
      Authors --> Articles;
      Events -- Probabilities --> Topics;
      Topics -- Probabilities --> Articles;
      Users -- Membership --> Segments;
      Users -- Preferences --> A[Page Views];
      Segments -- Rights --> A[Page Views];
      Articles --> A[Page Views];
```

```mermaid
  graph Generation;
      Authors --> Articles;
      Events -- Probabilities --> Topics;
      Topics -- Probabilities --> Articles;
      Users -- Membership --> Segments;
      Users -- Preferences --> A[Page Views];
      Segments -- Rights --> A[Page Views];
      Articles --> A[Page Views];
```

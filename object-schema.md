```mermaid
  graph TD;
      Authors --> Articles;
      Events -- Probabilities --> Topics;
      Topics -- Probabilities --> Articles;
      Useers -- Membership --> Segments;
      Users & Segments & Articles --> Page Views;
```

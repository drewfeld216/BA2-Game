```mermaid
  graph TD;
      Authors --> Articles;
      Events -- Probabilities --> Topics;
      Topics -- Probabilities --> Articles;
      Useers -- Membership --> Segments;
      Users --> Page Views;
      Segments --> Page Views;
      Articles --> Page Views;
```

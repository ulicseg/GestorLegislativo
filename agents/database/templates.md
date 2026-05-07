# Database Templates

## Example 1: Model with constraint
```python
class RutaComision(models.Model):
    proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE)
    comision = models.ForeignKey(Categoria, on_delete=models.CASCADE)

    class Meta:
        unique_together = ['proyecto', 'comision']
```

## Example 2: Migration note
```text
This migration adds a nullable field first, backfills data, and then tightens the constraint.
```

## Example 3: Data integrity check
```python
def clean(self):
    if self.numero and '/' not in self.numero:
        raise ValidationError({'numero': 'El numero debe tener formato XXXX/XX'})
```
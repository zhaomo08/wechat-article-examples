var book = new[] { new Stock("A", 12), new Stock("B", 8) };
var counted = new[] { new Stock("B", 6), new Stock("C", 4) };

var rows = book.FullJoin(
    counted,
    item => item.Sku,
    item => item.Sku,
    (left, right) => new
    {
        Sku = left?.Sku ?? right!.Sku,
        Book = left?.Quantity,
        Counted = right?.Quantity,
        Status = left is null ? "counted only"
            : right is null ? "book only"
            : left.Quantity == right.Quantity ? "same"
            : "quantity mismatch"
    });

Console.WriteLine("SKU  Book     Counted  Status");
foreach (var row in rows.OrderBy(row => row.Sku, StringComparer.Ordinal))
{
    Console.WriteLine($"{row.Sku,-5}{Display(row.Book),-9}{Display(row.Counted),-9}{row.Status}");
}

var duplicatePairs = new[] { new Stock("B", 5), new Stock("B", 3) }
    .FullJoin(new[] { new Stock("B", 2), new Stock("B", 4) },
        item => item.Sku,
        item => item.Sku,
        (left, right) => (left, right));
Console.WriteLine($"Duplicate B: {duplicatePairs.Count()} matched pairs");

static string Display(int? number) => number?.ToString() ?? "missing";

record Stock(string Sku, int Quantity);

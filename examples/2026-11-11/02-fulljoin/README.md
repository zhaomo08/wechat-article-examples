# 用 .NET 11 FullJoin 对两张库存表

要求 .NET 11 SDK。目录没有第三方 NuGet 包，数据为自造。

```sh
dotnet --version
dotnet run --project StockCheck.csproj
```

`output.txt` 是用 macOS ARM64 上的官方 .NET SDK 11.0.100 实际执行的输出。两个样例分别展示单边有记录时保留一整行，以及两边重复键会产生多组配对。这里验证的是内存中的 LINQ 查询，不涉及 Entity Framework Core 或数据库。

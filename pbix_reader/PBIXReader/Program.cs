using System;
using System.Linq;
using Microsoft.AnalysisServices.Tabular;
using Newtonsoft.Json;

namespace PBIXReader
{
    class Program
    {
        static void Main(string[] args)
        {
            // args: server, database
            string server = args[0];
            string database = args[1];

            Server s = new Server();
            s.Connect($"Provider=MSOLAP;Data Source={server};Initial Catalog={database}");
            var model = s.Databases[database].Model;

            var tables = model.Tables.Select(t => new {
                t.Name,
                Columns = t.Columns.Select(c => c.Name).ToArray(),
                Measures = t.Measures.Select(m => m.Name).ToArray()
            }).ToArray();

            Console.WriteLine(JsonConvert.SerializeObject(tables, Formatting.Indented));
        }
    }
}

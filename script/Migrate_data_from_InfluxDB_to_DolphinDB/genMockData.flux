import "influxdata/influxdb/sample"

sample.data(set: "machineProduction")
    |> to(bucket: "demo-bucket")
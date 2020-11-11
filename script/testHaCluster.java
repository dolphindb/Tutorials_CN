import com.xxdb.DBConnection;
import com.xxdb.data.BasicLong;
import com.xxdb.data.BasicTable;
import com.xxdb.data.Entity;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

public class cluster2 {


    public static DBConnection conn;
    public static String[] sites = {"192.168.1.12:22217", "192.168.1.12:22218", "192.168.1.13:22217", "192.168.1.13:22218", "192.168.1.14:22217", "192.168.1.14:22218"};

    public static void main(String[] args) throws IOException, InterruptedException {
        conn = new DBConnection();
        boolean b = conn.connect("192.168.1.12:22217", 22217, "admin", "123456", "", true, sites);
        String script = "login(`admin,`123456)\n" +
                "if(existsDatabase(\"dfs://javaAPItest2\")){dropDatabase(\"dfs://javaAPItest2\")};\n" +
                "db=database(\"dfs://javaAPItest2\",VALUE,2018.08.01..2018.08.10);\n" +
                "t=table(2018.08.01..2018.08.10 as date ,1..10 as id);\n" +
                "pt=db.createPartitionedTable(t,`pt,`date);\n" +
                "retentionHour=3*24\n" +
                "setRetentionPolicy(db,retentionHour,0);\n";
        conn.run(script);
        int i = 1;
        BasicLong res;
        while (b) {
            try {
                if (i < 1000) {
                    String s = "t = table(take(2018.08.01..2018.08.10 ," + i + ") as date ,take(1.." + i + "," + i + ") as id);" + "pt=loadTable(\"dfs://javaAPItest2\",`pt);pt.append!(t);exec count(*) from pt ";
                    res = (BasicLong) conn.run(s);
                } else {
                    String s = "t = table(take(2018.08.01..2018.08.10 ,100) as date ,rand("+i+",100) as id);" + "pt=loadTable(\"dfs://javaAPItest2\",`pt);pt.append!(t);exec count(*) from pt ";
                    res = (BasicLong) conn.run(s);
                   }
                    System.out.println(i + "=" + res.getLong());
                }catch(Exception ex){
                    ex.printStackTrace();
                }
                i++;
            }
        }
    }
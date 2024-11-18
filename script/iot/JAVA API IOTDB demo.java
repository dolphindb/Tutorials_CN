import com.xxdb.DBConnection;
import com.xxdb.data.*;
import com.xxdb.route.AutoFitTableAppender;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.Random;
import java.util.Vector;
import com.xxdb.DBConnection;
import com.xxdb.route.AutoFitTableAppender;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
public class Main {

    public static void main(String[] args) throws Exception {

        String ipAddress="";
        int ipPort=8848;
        String user="admin";
        String password="123456";
        DBConnection dbConnection = new DBConnection();
        dbConnection.connect(ipAddress, ipPort,user,password);
        // 先创建一张表
        dbConnection.run("if (exists(\"dfs://IOTDB\")){\n" +
                "    dropDatabase(\"dfs://IOTDB\")\n" +
                "}"+"create database \"dfs://IOTDB\" partitioned by HASH([SYMBOL,10]),VALUE([today()]),engine = \"IOTDB\"; "+"create table \"dfs://IOTDB\".\"data\" (\n" +
                "        Time TIMESTAMP [compress = \"delta\"],\n" +
                "        ID SYMBOL,\n" +
                "        Value IOTANY,\n" +
                "        StaticInfo SYMBOL \n" +
                ")\n" +
                "partitioned by ID, Time,\n" +
                "sortColumns = [\"ID\",\"Time\"],\n" +
                "latestKeyCache = true");
        int size=100000;
        // 准备要写入的表
        //TimeStamp (time列)
        BasicTimestampVector timeVector=new BasicTimestampVector(size);
        //SYMBOL（ID列）
        BasicSymbolVector idVector=new BasicSymbolVector(size);

        //double(value 列)
        BasicDoubleVector doubleVector=new BasicDoubleVector(size);
        //bool（balue 列）
        BasicBooleanVector booleanVector=new BasicBooleanVector(size);
        //string（value列）
        BasicStringVector stringVector=new BasicStringVector(size);

        //SYMBOL（staticInfo列）
        BasicSymbolVector staticInfoVector=new BasicSymbolVector(size);

        //写入double格式数据
        Random rand=new Random();
        for(int i=0;i<size;++i){
            LocalDateTime dt=LocalDateTime.now();
            timeVector.setTimestamp(i,dt);
            idVector.setString(i,"chloramine_"+i);
            doubleVector.setDouble(i,rand.nextDouble());
            staticInfoVector.setString(i,"SZ");
        }
        ArrayList<com.xxdb.data.Vector> cols=new ArrayList<>();
        cols.add(timeVector);
        cols.add(idVector);
        cols.add(doubleVector);
        cols.add(staticInfoVector);
        ArrayList<String> colName=new ArrayList<>();
        colName.add("Time");
        colName.add("ID");
        colName.add("Value");
        colName.add("StaticInfo");
        BasicTable insertTable = new BasicTable(colName, cols);
        AutoFitTableAppender appender=new AutoFitTableAppender("dfs://IOTDB","data",dbConnection);
        appender.append(insertTable);


        //写入bool格式数据
        for(int i=0;i<size;++i){
            LocalDateTime dt=LocalDateTime.now();
            timeVector.setTimestamp(i,dt);
            idVector.setString(i,"valve_"+i);
            booleanVector.setBoolean(i,rand.nextBoolean());
            staticInfoVector.setString(i,"BJ");
        }
        cols=new ArrayList<>();
        cols.add(timeVector);
        cols.add(idVector);
        cols.add(booleanVector);
        cols.add(staticInfoVector);
        colName=new ArrayList<>();
        colName.add("Time");
        colName.add("ID");
        colName.add("Value");
        colName.add("StaticInfo");
        insertTable = new BasicTable(colName, cols);
        appender=new AutoFitTableAppender("dfs://IOTDB","data",dbConnection);
        appender.append(insertTable);

        //写入string格式数据
        for(int i=0;i<size;++i){
            LocalDateTime dt=LocalDateTime.now();
            timeVector.setTimestamp(i,dt);
            idVector.setString(i,"tatus_"+i);
            stringVector.setString(i,"GBXF_001");
            staticInfoVector.setString(i,"SH");
        }
        cols=new ArrayList<>();
        cols.add(timeVector);
        cols.add(idVector);
        cols.add(stringVector);
        cols.add(staticInfoVector);
        colName=new ArrayList<>();
        colName.add("Time");
        colName.add("ID");
        colName.add("Value");
        colName.add("StaticInfo");
        insertTable = new BasicTable(colName, cols);
        appender=new AutoFitTableAppender("dfs://IOTDB","data",dbConnection);
        appender.append(insertTable);




    }

}

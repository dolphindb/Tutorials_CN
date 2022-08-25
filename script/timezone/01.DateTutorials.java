import java.io.IOException;
import java.io.Reader;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.Arrays;
import java.util.LinkedList;
import java.util.List;

import com.opencsv.CSVReader;
import com.opencsv.exceptions.CsvValidationException;
import com.xxdb.DBConnection;
import com.xxdb.comm.ErrorCodeInfo;
import com.xxdb.data.*;
import com.xxdb.multithreadedtablewriter.MultithreadedTableWriter;

public class DateTest {

	private static final String CSV = "./lib/taq.csv";

	private static final DBConnection conn = new DBConnection();
	static {
		try {
			conn.connect("localhost", 8848, "admin", "123456");
			conn.run("t = table(100:0,`symbol`datetime`bid`ofr`bidsize`ofrsize`mode`ex`mmid,[SYMBOL,DATETIME,DOUBLE,DOUBLE,LONG,LONG,INT,CHAR,SYMBOL])\n" +
					"share t as timeTest;");
		} catch (IOException e) {
			e.printStackTrace();
		}
	}

	public static int getTime(String timeStr){
		DateTimeFormatter df = DateTimeFormatter.ofPattern("yyyy.MM.dd H:mm:ss");
		LocalDateTime ldt = LocalDateTime.parse(timeStr,df);
		return Utils.countSeconds(ldt);
	}

	public static LocalDateTime getDateTime(String timeStr){
		DateTimeFormatter df = DateTimeFormatter.ofPattern("yyyy.MM.dd H:mm:ss");
		LocalDateTime ldt = LocalDateTime.parse(timeStr,df);
		return ldt;
	}

	public static void write() throws IOException {
		LinkedList<String> symbolList = new LinkedList<>();// symbol
		LinkedList<Integer> dtList = new LinkedList<>();// datetime
		LinkedList<Double> bidList = new LinkedList<>();// bid
		LinkedList<Double> ofrList = new LinkedList<>();// ofr
		LinkedList<Long> bidSizeList = new LinkedList<>();// bidSize
		LinkedList<Long> ofrSizeList = new LinkedList<>();// ofrSize
		LinkedList<Integer> modeList = new LinkedList<>();// mode
		LinkedList<Byte> exList = new LinkedList<>();// ex
		LinkedList<String> mmidList = new LinkedList<>();// mmid

		try (Reader reader = Files.newBufferedReader(Paths.get(CSV));
			 CSVReader csvReader = new CSVReader(reader)) {

			String[] record;
			csvReader.readNext();// skip first line
			while ((record = csvReader.readNext()) != null) {
				symbolList.add(record[0]);
				dtList.add(getTime(record[1]+" "+record[2]));
				bidList.add(Double.parseDouble(record[3]));
				ofrList.add(Double.parseDouble(record[4]));
				bidSizeList.add(Long.parseLong(record[5]));
				ofrSizeList.add(Long.parseLong(record[6]));
				modeList.add(Integer.parseInt(record[7]));
				exList.add((byte)record[8].charAt(1));
				mmidList.add(record[9]);
			}
		} catch (IOException | CsvValidationException ex) {
			ex.printStackTrace();
		}

		List<Entity> data = Arrays.asList(
				new BasicSymbolVector(symbolList),
				new BasicDateTimeVector(dtList),
				new BasicDoubleVector(bidList),
				new BasicDoubleVector(ofrList),
				new BasicLongVector(bidSizeList),
				new BasicLongVector(ofrSizeList),
				new BasicIntVector(modeList),
				new BasicByteVector(exList),
				new BasicSymbolVector(mmidList)
		);
		conn.run("tableInsert{\"timeTest\"}", data);
	}

	public static void mtwWrite(){
		final int batchSize = 10000;
		final int throttle = 1;
		final int threadCount = 1;
		final String partitionCol = "datetime";
		ErrorCodeInfo pErrorInfo=new ErrorCodeInfo();
		MultithreadedTableWriter multithreadedTableWriter = null;
		try {
			multithreadedTableWriter = new MultithreadedTableWriter("localhost", 8848, "admin", "123456", "timeTest", "",
					false, false, null, batchSize, throttle, threadCount, partitionCol);
		} catch (Exception e) {
			e.printStackTrace();
		}
		try (Reader reader = Files.newBufferedReader(Paths.get(CSV));
			 CSVReader csvReader = new CSVReader(reader)) {
			String[] record;
			csvReader.readNext();// skip first line
			while ((record = csvReader.readNext()) != null) {
				multithreadedTableWriter.insert(pErrorInfo,
						record[0],
						getDateTime(record[1]+" "+record[2]),
						Double.parseDouble(record[3]),
						Double.parseDouble(record[4]),
						Long.parseLong(record[5]),
						Long.parseLong(record[6]),
						Integer.parseInt(record[7]),
						(byte)record[8].charAt(1),
						record[9]
				);
			}
			multithreadedTableWriter.waitForThreadCompletion();
		} catch (IOException | CsvValidationException | InterruptedException ex) {
			ex.printStackTrace();
		}
	}

	public static void select() throws IOException {
		BasicTable res = (BasicTable)conn.run("select * from timeTest");
		System.out.println(res.getString());
	}

	public static void main(String[] args) throws IOException {
//		mtwWrite();
		select();
	}
}

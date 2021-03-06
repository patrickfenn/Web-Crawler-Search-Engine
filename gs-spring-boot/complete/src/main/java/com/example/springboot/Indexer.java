package com.example.springboot;


import org.apache.lucene.analysis.standard.StandardAnalyzer;
import org.apache.lucene.document.Document;
import org.apache.lucene.document.Field;
import org.apache.lucene.document.StringField;
import org.apache.lucene.document.TextField;
import org.apache.lucene.index.CorruptIndexException;
import org.apache.lucene.index.DirectoryReader;
import org.apache.lucene.index.IndexWriter;
import org.apache.lucene.index.IndexWriterConfig;
import org.apache.lucene.search.IndexSearcher;
import org.apache.lucene.search.Query;
import org.apache.lucene.search.ScoreDoc;
import org.apache.lucene.store.Directory;
import org.apache.lucene.store.FSDirectory;
import org.apache.lucene.util.QueryBuilder;
import org.json.simple.JSONArray;
import org.json.simple.JSONObject;
import org.json.simple.parser.JSONParser;
import org.json.simple.parser.ParseException;

import java.io.File;
import java.io.FileReader;
import java.io.IOException;


import java.nio.file.Path;
import java.util.Iterator; //json parsing

import java.util.*;

import com.google.gson.Gson; 
import com.google.gson.GsonBuilder; 


public class Indexer {
    private final String file_name = "Data2.json";
    private IndexWriter writer;
    //private String indexDir;
    private StandardAnalyzer analyzer; //tokenifies the document
    private Directory indexDirectory; //directory of the index
    private IndexSearcher isearcher; //
    private QueryBuilder builder;
    private int counter;

    //constructor, assigns writer
    //  json file in project root ./Data.json
    //  index file in Index folder in project root
    public Indexer () throws IOException 
    {
        counter = 0;
        String workingDir = System.getProperty("user.dir");
        String indexDir = workingDir+"\\Index";
        //index directory, .open takes a 'Path type'
        Path path = (new File(indexDir)).toPath();
        indexDirectory = FSDirectory.open(path); 

        //create the indexer: writer    
        analyzer = new StandardAnalyzer();
        IndexWriterConfig conf = new IndexWriterConfig(analyzer);
        writer = new IndexWriter(indexDirectory,conf);

        try {
            //  json file in project root folder
            this.indexFile(file_name);
            this.close(); 
            this.initializeSearcher();

            //parseJSON();
        } catch (Exception e) {
            
            e.printStackTrace();
            System.out.println("unable to read file, exiting...");
            System.exit(1);
        }

        
    }
    private void initializeSearcher() throws IOException
    {
        DirectoryReader ireader = DirectoryReader.open(indexDirectory);
        isearcher = new IndexSearcher(ireader);
        builder = new QueryBuilder(analyzer);

    }
    //destructor
    protected void finalize() throws CorruptIndexException, IOException 
    {
        
    }
    //closes the writer
    public void close() throws CorruptIndexException, IOException {
        writer.close();
    }

    //Return a Document object for the indexer from the passed doc JSONObject
    //reference:
    //https://www.tutorialspoint.com/lucene/lucene_adddocument.htm
    public Document getDocument(JSONObject doc) {
        Document document = new Document();
  
        //index file contents
        //Field contentField = new TextField("contents", new FileReader(file));


        Field contentField = new TextField("content",  (String) doc.get("content"), Field.Store.YES); //don't store body in index
        Field titleField = new StringField("title",(String) doc.get("title"),Field.Store.YES);
        Field URLField = new StringField("url",(String) doc.get("url"),Field.Store.YES);
  
        document.add(contentField);
        document.add(titleField);
        document.add(URLField);

        //System.out.println(doc.get("title"));


        return document;
     }




    //Indexes a data file which is a JSONArray
    //Splits the array into objects
    //Converts objects into documents
    //Adds documents to the indexWriter
    private void indexFile(String fileName) throws IOException, ParseException {
        System.out.println("Indexing "+fileName);

        
        //Open the data file
        JSONArray ja = openJSON(fileName);
        if(ja == null) System.exit(1);
        
            
        
        //Iterate through each JSONObject in the JSONArray
        Iterator iteratorDocs = ja.iterator();
        
        while (iteratorDocs.hasNext())
        {
            JSONObject doc = (JSONObject) iteratorDocs.next();
            Document document = getDocument(doc);
            writer.addDocument(document); //add the document to the index
        }

        
        
     }
    
    public String search(String queryText, int numResults) throws IOException
     {
        String field = "content";

        Query q = builder.createPhraseQuery(field, queryText);
        ScoreDoc[] hits = isearcher.search(q, numResults).scoreDocs;

        LinkedHashSet<JSONObject> set=new LinkedHashSet();  
        

        for (int i = 0; i < hits.length; i++) {
            Document hitDoc = isearcher.doc(hits[i].doc);
            JSONObject result_map = new JSONObject();

            String title = hitDoc.get("title");
            String url = hitDoc.get("url");
            String content = hitDoc.get("content");
            String score = String.format("%.3f", hits[i].score);

            String snip = (new Snippet()).generateSnippet(queryText,content);

            result_map.put("title", title);
            result_map.put("url", url);
            result_map.put("content", snip);
            result_map.put("score", score);
            result_map.put("id", String.valueOf(counter));
            counter++;


            set.add(result_map);

            


          }

 
        return new Gson().toJson(set );
     }
     public String search(String queryText,String field) throws IOException
     {
        int numResults = 10;
        Query q = builder.createPhraseQuery(field, queryText);
        ScoreDoc[] hits = isearcher.search(q, numResults).scoreDocs;
        
        String returnedStr = "";
        for (int i = 0; i < hits.length; i++) {
            Document hitDoc = isearcher.doc(hits[i].doc);
            returnedStr += hitDoc.get("title") + "\n";
            //returnedStr += hitDoc.get("url") + "\n";

          }

        return returnedStr;
     }

     //
     //reference: https://www.geeksforgeeks.org/parse-json-java/
     //throws exception fixes error message
     public static JSONArray openJSON(String fileName) 
        throws IOException, ParseException {
            //get all files in the data directory
            String filePath = System.getProperty("user.dir") + "/"+fileName;
            File file = new File(filePath);
            JSONArray ja = null;
            if(!file.isDirectory()
                  && !file.isHidden()
                  && file.exists()
                  && file.canRead()
                  //&& filter.accept(file) //import java.io.FileFilter;

               ){
                Object obj = new JSONParser().parse(new FileReader(fileName));
                ja = (JSONArray) obj;
               }
            else
            {
                System.out.println("Invalid filepath: "+filePath);
                System.exit(1);
            }

        return ja;

     }
      

}


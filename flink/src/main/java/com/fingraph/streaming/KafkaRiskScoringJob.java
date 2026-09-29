package com.fingraph.streaming;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import org.apache.flink.api.common.eventtime.WatermarkStrategy;
import org.apache.flink.api.common.serialization.SimpleStringSchema;
import org.apache.flink.connector.base.DeliveryGuarantee;
import org.apache.flink.connector.kafka.sink.KafkaRecordSerializationSchema;
import org.apache.flink.connector.kafka.sink.KafkaSink;
import org.apache.flink.connector.kafka.source.KafkaSource;
import org.apache.flink.connector.kafka.source.enumerator.initializer.OffsetsInitializer;
import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment;

public class KafkaRiskScoringJob {
    public static void main(String[] args) throws Exception {
        StreamExecutionEnvironment env =
                StreamExecutionEnvironment.getExecutionEnvironment();
        env.setParallelism(1);

        KafkaSource<String> source = KafkaSource.<String>builder()
                .setBootstrapServers("kafka:19092")
                .setTopics("transactions")
                .setGroupId("fingraph-flink")
                .setStartingOffsets(OffsetsInitializer.earliest())
                .setValueOnlyDeserializer(new SimpleStringSchema())
                .build();

        KafkaSink<String> sink = KafkaSink.<String>builder()
                .setBootstrapServers("kafka:19092")
                .setRecordSerializer(
                        KafkaRecordSerializationSchema.<String>builder()
                                .setTopic("transactions-processed")
                                .setValueSerializationSchema(
                                        new SimpleStringSchema())
                                .build())
                .setDeliveryGuarantee(DeliveryGuarantee.AT_LEAST_ONCE)
                .build();

        env.fromSource(
                        source,
                        WatermarkStrategy.noWatermarks(),
                        "Kafka transactions")
                .map(KafkaRiskScoringJob::addRiskScore)
                .sinkTo(sink);

        env.execute("FinGraph transaction risk scoring");
    }

    private static String addRiskScore(String rawEvent) {
        JsonObject event = JsonParser.parseString(rawEvent).getAsJsonObject();
        double amount = event.get("amount").getAsDouble();

        double score;
        if (amount >= 4000) {
            score = 0.8;
        } else if (amount >= 1000) {
            score = 0.4;
        } else {
            score = 0.1;
        }

        event.addProperty("risk_score", score);
        event.addProperty("flink_processed", true);
        return event.toString();
    }
}
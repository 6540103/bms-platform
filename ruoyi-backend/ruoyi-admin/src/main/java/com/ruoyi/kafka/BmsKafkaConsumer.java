package com.ruoyi.kafka;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.ruoyi.system.domain.BmsRealtimeData;
import com.ruoyi.system.service.IBmsRealtimeDataService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Component;

/**
 * BMS Kafka消费者 - 监听电池实时数据和事件
 */
@Component
public class BmsKafkaConsumer
{
    private static final Logger log = LoggerFactory.getLogger(BmsKafkaConsumer.class);

    @Autowired
    private IBmsRealtimeDataService bmsRealtimeDataService;

    private final ObjectMapper objectMapper = new ObjectMapper();

    // 每N条存一条到数据库
    private static final int SAVE_INTERVAL = 10;
    private int messageCount = 0;

    @KafkaListener(topics = "bms.realtime", groupId = "ruoyi-bms-consumer")
    public void consumeRealtime(String message)
    {
        try
        {
            JsonNode node = objectMapper.readTree(message);
            messageCount++;

            if (messageCount % SAVE_INTERVAL == 0)
            {
                BmsRealtimeData data = parseRealtimeData(node);
                bmsRealtimeDataService.insertBmsRealtimeData(data);
                log.debug("Saved BMS realtime data #{}: SOC={}%, V={}V, status={}",
                        messageCount, data.getSoc(), data.getPackVoltage(), data.getStatus());
            }
        }
        catch (Exception e)
        {
            log.error("解析BMS实时数据失败: {}", e.getMessage());
        }
    }

    @KafkaListener(topics = "bms.events", groupId = "ruoyi-bms-consumer")
    public void consumeEvents(String message)
    {
        try
        {
            JsonNode node = objectMapper.readTree(message);
            String event = node.path("event").asText();
            log.info("收到BMS事件: {}", event);
        }
        catch (Exception e)
        {
            log.error("解析BMS事件失败: {}", e.getMessage());
        }
    }

    private BmsRealtimeData parseRealtimeData(JsonNode node)
    {
        BmsRealtimeData data = new BmsRealtimeData();
        data.setSimTime(node.path("sim_time").asDouble());
        data.setPackVoltage(node.path("pack_voltage").asDouble());
        data.setCurrent(node.path("current").asDouble());
        data.setPower(node.path("power").asDouble());
        data.setSoc(node.path("soc").asDouble());
        data.setSoh(node.path("soh").asDouble());
        data.setMinCellVoltage(node.path("min_cell_voltage").asDouble());
        data.setMaxCellVoltage(node.path("max_cell_voltage").asDouble());
        data.setVoltageImbalance(node.path("voltage_imbalance").asDouble());

        JsonNode tempNode = node.path("temperature");
        if (tempNode.isArray() && tempNode.size() >= 2)
        {
            data.setTemperature(tempNode.get(0).asDouble());
            data.setAmbientTemp(tempNode.get(1).asDouble());
        }

        data.setStatus(node.path("status").asText());
        data.setCellVoltage(node.path("cell_voltage").toString());
        data.setCellSoc(node.path("cell_soc").toString());
        data.setCapacityAh(node.path("capacity_ah").asDouble());
        data.setCycleCount(node.path("cycle_count").asInt());
        data.setNumCells(node.path("num_cells").asInt());

        // 保存完整BMS状态JSON
        JsonNode bmsNode = node.path("bms");
        if (bmsNode != null && !bmsNode.isMissingNode() && !bmsNode.isNull())
        {
            try
            {
                data.setBmsStatus(objectMapper.writeValueAsString(bmsNode));
            }
            catch (Exception e)
            {
                log.warn("序列化BMS状态失败: {}", e.getMessage());
            }
        }

        return data;
    }
}

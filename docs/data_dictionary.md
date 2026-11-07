# 数据字典 · Olist Brazilian E-Commerce

> 数据来源：Kaggle — Brazilian E-Commerce Public Dataset by Olist
> 规模：9 张表 / 1,556,417 行 / 解压后 120 MB / 2016-09 ~ 2018-10
> 说明：本文档记录每个字段的含义、**在分析中的角色**、以及已知的数据质量问题。

## 一、表清单

| # | 表 | 行数 | 主键 | 粒度（一行 = 什么） |
|---|---|---|---|---|
| 1 | `orders` | 99,441 | `order_id` | 一个订单 |
| 2 | `order_items` | 112,650 | `order_id` + `order_item_id` | 订单里的一个商品项 |
| 3 | `order_payments` | 103,886 | `order_id` + `payment_sequential` | 一次支付动作 |
| 4 | `order_reviews` | 99,224 | `review_id` + `order_id` | 一条评价 |
| 5 | `customers` | 99,441 | `customer_id` | **一张订单的客户记录**（不是一个人） |
| 6 | `products` | 32,951 | `product_id` | 一个商品 |
| 7 | `sellers` | 3,095 | `seller_id` | 一个卖家 |
| 8 | `geolocation` | 1,000,163 | 无 | 一条邮编-坐标对 |
| 9 | `product_category_name_translation` | 71 | `product_category_name` | 一个品类的翻译 |

## 二、表关系

```
                        ┌── products ── product_category_name ── translation
                        │
orders ──customer_id──> customers ──zip_code_prefix──> geolocation
  │  │
  │  ├──order_id──> order_items ──seller_id──> sellers
  │  │
  │  ├──order_id──> order_payments
  │  │
  │  └──order_id──> order_reviews
  │
  └── 4 个时间戳：purchase / approved / carrier / delivered
      + 1 个承诺日：estimated_delivery
```

## 三、字段明细

### 1. `orders`（订单主表）

| 字段 | 类型 | 含义 | 分析角色 | 用于宽表 |
|---|---|---|---|---|
| `order_id` | VARCHAR(32) | 订单号 | 主键，连接 4 张表 | ✅ |
| `customer_id` | VARCHAR(32) | 订单级客户号 | 连 `customers`（一单一号） | — |
| `order_status` | VARCHAR | 订单状态（8 种） | **筛选口径** | ✅ |
| `order_purchase_timestamp` | DATETIME | 下单时间 | 时间轴起点 | ✅ |
| `order_approved_at` | DATETIME | 支付批准时间 | 履约第 1 段 | — |
| `order_delivered_carrier_date` | DATETIME | 交运时间 | 履约第 2 段 | — |
| `order_delivered_customer_date` | DATETIME | 送达时间 | **履约终点** | ✅ |
| `order_estimated_delivery_date` | DATETIME | **承诺送达日** | **超时分母** | ✅ |

### 2. `order_items`（订单明细）

| 字段 | 类型 | 含义 | 分析角色 | 用于宽表 |
|---|---|---|---|---|
| `order_id` | VARCHAR(32) | 订单号 | 外键 | ✅ |
| `order_item_id` | INT | 明细序号 | 复合主键 | — |
| `product_id` | VARCHAR(32) | 商品号 | 连 `products` | — |
| `seller_id` | VARCHAR(32) | 卖家号 | 连 `sellers` | — |
| `shipping_limit_date` | DATETIME | 卖家承诺发货截止 | 卖家履约 | — |
| `price` | DECIMAL(12,2) | 商品单价 | **GMV 唯一来源** | ✅ |
| `freight_value` | DECIMAL(12,2) | 运费 | 物流成本代理 | ✅ |

> **金额藏在明细层，不在订单表。** 任何 GMV 分析都必须先聚合到订单粒度。

### 3. `order_payments`（支付）

| 字段 | 类型 | 含义 | 分析角色 | 用于宽表 |
|---|---|---|---|---|
| `order_id` | VARCHAR(32) | 订单号 | 外键 | ✅ |
| `payment_sequential` | INT | 第几笔支付 | 一单可多笔 | — |
| `payment_type` | VARCHAR(30) | credit_card / boleto / voucher / debit_card | 支付结构 | ✅ |
| `payment_installments` | INT | 分期数 | 消费力代理 | — |
| `payment_value` | DECIMAL(12,2) | 本次支付金额 | 与 `price+freight` 对账 | ✅ |

### 4. `order_reviews`（评价）

| 字段 | 类型 | 含义 | 分析角色 | 用于宽表 |
|---|---|---|---|---|
| `review_id` | VARCHAR(32) | 评价号 | ⚠️ 不唯一（814 行重复） | — |
| `order_id` | VARCHAR(32) | 订单号 | 连订单 | ✅ |
| `review_score` | INT (1–5) | **评分** | **核心因变量** | ✅ |
| `review_comment_title` | TEXT | 标题 | 88.3% 为空 | — |
| `review_comment_message` | TEXT | 正文 | 58.7% 为空 | — |
| `review_creation_date` | DATETIME | 评价时间 | 时效 | — |
| `review_answer_timestamp` | DATETIME | 平台回复时间 | 客服响应 | — |

### 5. `customers`（客户）

| 字段 | 类型 | 含义 | 分析角色 | 用于宽表 |
|---|---|---|---|---|
| `customer_id` | VARCHAR(32) | **订单级**客户号 | ⚠️ 一单一号，不能算复购 | — |
| `customer_unique_id` | VARCHAR(32) | **真实用户号**（96,096） | **复购/分层依据** | ✅ |
| `customer_zip_code_prefix` | INT | 邮编前 5 位 | 地理 | — |
| `customer_city` | VARCHAR(80) | 城市 | 地理 | — |
| `customer_state` | VARCHAR(2) | 州（27 个） | **地域主维度** | ✅ |

### 6. `products`（商品）

| 字段 | 类型 | 含义 | 分析角色 | 用于宽表 |
|---|---|---|---|---|
| `product_id` | VARCHAR(32) | 商品号 | 主键 | — |
| `product_category_name` | VARCHAR(100) | 品类（葡语） | 品类分析 | — |
| `product_name_lenght` | INT | 名称长度 | ⚠️ 原数据拼写错误 | — |
| `product_description_lenght` | INT | 描述长度 | 同上 | — |
| `product_photos_qty` | INT | 图片数 | 转化代理（无转化数据） | — |
| `product_weight_g` | INT | 重量（克） | 运费归因 | — |
| `product_length_cm` / `height_cm` / `width_cm` | INT | 尺寸 | 大件识别 | — |

### 7. `sellers`（卖家）

| 字段 | 类型 | 含义 | 分析角色 | 用于宽表 |
|---|---|---|---|---|
| `seller_id` | VARCHAR(32) | 卖家号 | 主键 | — |
| `seller_zip_code_prefix` | INT | 邮编 | 发货地 | — |
| `seller_city` / `seller_state` | VARCHAR | 城市 / 州 | 发货地 vs 收货地 | — |

### 8. `geolocation`（地理坐标）

| 字段 | 类型 | 含义 | 分析角色 | 用于宽表 |
|---|---|---|---|---|
| `geolocation_zip_code_prefix` | INT | 邮编 | 连接键 | ❌ 未使用 |
| `geolocation_lat` / `lng` | DECIMAL | 经纬度 | 距离计算 | ❌ 未使用 |
| `geolocation_city` / `state` | VARCHAR | 城市 / 州 | 与 customers 冗余 | ❌ 未使用 |

> 100 万行只对应 19,015 个邮编，**平均每邮编 52 行**。做地理距离分析要先按邮编聚合，成本高、收益低，本项目主动放弃。

### 9. `product_category_name_translation`（品类翻译）

| 字段 | 类型 | 含义 | 分析角色 | 用于宽表 |
|---|---|---|---|---|
| `product_category_name` | VARCHAR(100) | 葡语品类名 | 连接键 | ✅ |
| `product_category_name_english` | VARCHAR(100) | 英文品类名 | 可读的品类名 | ✅ |

## 四、已知数据质量问题（均为实测）

| # | 问题 | 规模 | 影响 | 处理方式 |
|---|---|---|---|---|
| 1 | 物流日期为空字符串 | 2,980 行 | 严格模式下导入静默丢 3% | 先入字符串再转 NULL |
| 2 | `review_id` 重复 | 789 个 ID / 814 行 | 单列主键挡掉 814 条 | 改用 `(review_id, order_id)` 复合主键 |
| 3 | 评论含换行符 | 3,852 条 | CSV 解析错行，少 815 条 | 只导评分等定长字段 |
| 4 | 品类缺失 | 610 个商品 | 占比分母差 1.33% | 归入「未标注品类」，图注说明 |
| 5 | 翻译表缺 2 个品类 | 13 个商品 | JOIN 匹配不上 | 按葡语意译补齐 |
| 6 | 有支付无明细 | 775 单 | INNER JOIN 丢单 | 报告说明，不影响 GMV |
| 7 | `customers` 表 99,441 行 | = 订单数 | 用 `customer_id` 算复购率恒为 0 | 改用 `customer_unique_id` |

## 五、字段使用情况

9 张表共 **52 个字段**，实际参与分析的有 15 个（29%）：

| 用途 | 字段 | 数量 |
|---|---|---|
| 订单宽表 `order_wide` 的源字段 | `order_id`、`customer_unique_id`、`customer_state`、`order_status`、`order_purchase_timestamp`、`order_delivered_customer_date`、`order_estimated_delivery_date`、`price`、`freight_value` | 9 |
| 品类维度 | `product_id`、`product_category_name`、`product_category_name_english` | 3 |
| 评分与支付 | `review_score`、`payment_type`、`payment_value` | 3 |

> 宽表本身 11 列，其中 `buy_month`（下单年月）与 `item_cnt`（明细行数）是派生列。

核心因果链只依赖 7 个字段：`order_id`、三个时间戳（下单 / 送达 / 承诺）、`price`、`review_score`、`customer_unique_id`。

**未参与计算的字段并非无用**：

- `geolocation`、`payment_installments` —— 探查阶段看过分布后判断「这条路收益低」，主动放弃
- `customer_state`、`product_category_name` —— 不进入因果链，但用于分州、分品类验证，排除混杂解释
- `payment_value` —— 只用于与明细金额对账（见 `reconciliation_log.md` 第 7 条）

## 六、口径定义（复现用）

| 指标 | 定义 | 备注 |
|---|---|---|
| 样本范围 | `order_status = 'delivered'` | 96,478 单，占 97% |
| GMV | `SUM(price)` | 不含运费；运费单列 `freight` |
| AOV | 总 GMV ÷ 总订单数 | 137.04（含运费 159.83） |
| 配送天数 | `DATEDIFF(delivered_ts, purchase_ts)` | **按整天截断** |
| 超时 | `DATEDIFF(delivered_ts, estimated_ts) > 0` | 按整天：6.77%；按小时：8.11% |
| 复购 | `customer_unique_id` 名下订单 ≥ 2 | 全量 3.12%；控制观察期后 5.51% |
| 差评 | `review_score <= 2` | 12.77% |
| 时间窗 | 2017-01 ~ 2018-08 | 首尾月份不完整，已截断 |

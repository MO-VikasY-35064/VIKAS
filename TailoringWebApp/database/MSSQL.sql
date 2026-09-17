USE [TailoringDB]
GO
/****** Object:  Table [dbo].[admin_users]    Script Date: 14-09-2026 16:20:48 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[admin_users](
	[id] [int] IDENTITY(1,1) NOT NULL,
	[username] [nvarchar](100) NOT NULL,
	[password_hash] [nvarchar](255) NOT NULL,
	[full_name] [nvarchar](200) NULL,
	[is_active] [bit] NOT NULL,
	[failed_attempts] [int] NOT NULL,
	[locked_until] [datetime2](7) NULL,
	[created_at] [datetime2](7) NOT NULL,
PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY],
UNIQUE NONCLUSTERED 
(
	[username] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[audit_logs]    Script Date: 14-09-2026 16:20:48 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[audit_logs](
	[id] [int] IDENTITY(1,1) NOT NULL,
	[admin_user] [nvarchar](100) NULL,
	[action] [nvarchar](100) NULL,
	[module] [nvarchar](100) NULL,
	[record_id] [nvarchar](100) NULL,
	[old_value] [nvarchar](max) NULL,
	[new_value] [nvarchar](max) NULL,
	[created_at] [datetime2](7) NOT NULL,
	[ip_address] [nvarchar](50) NULL,
PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO
/****** Object:  Table [dbo].[customers]    Script Date: 14-09-2026 16:20:48 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[customers](
	[id] [int] IDENTITY(1,1) NOT NULL,
	[mobile] [nvarchar](20) NOT NULL,
	[password_hash] [nvarchar](255) NOT NULL,
	[name] [nvarchar](200) NULL,
	[email] [nvarchar](255) NULL,
	[address] [nvarchar](500) NULL,
	[is_active] [bit] NOT NULL,
	[created_at] [datetime2](7) NOT NULL,
PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY],
UNIQUE NONCLUSTERED 
(
	[mobile] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[designs]    Script Date: 14-09-2026 16:20:48 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[designs](
	[id] [int] IDENTITY(1,1) NOT NULL,
	[name] [nvarchar](200) NOT NULL,
	[description] [nvarchar](1000) NULL,
	[category] [nvarchar](100) NULL,
	[neck_style] [nvarchar](100) NULL,
	[sleeve_style] [nvarchar](100) NULL,
	[blouse_length] [nvarchar](100) NULL,
	[customisation_details] [nvarchar](1000) NULL,
	[base_price] [decimal](10, 2) NOT NULL,
	[additional_charges] [decimal](10, 2) NOT NULL,
	[image_path] [nvarchar](500) NULL,
	[status] [nvarchar](20) NOT NULL,
	[created_at] [datetime2](7) NOT NULL,
	[modified_at] [datetime2](7) NOT NULL,
PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[email_logs]    Script Date: 14-09-2026 16:20:48 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[email_logs](
	[id] [int] IDENTITY(1,1) NOT NULL,
	[order_id] [int] NULL,
	[customer_id] [int] NULL,
	[email_to] [nvarchar](255) NULL,
	[email_type] [nvarchar](50) NULL,
	[sent_at] [datetime2](7) NOT NULL,
	[status] [nvarchar](20) NOT NULL,
	[error_message] [nvarchar](1000) NULL,
	[retry_count] [int] NOT NULL,
PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[gallery]    Script Date: 14-09-2026 16:20:48 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[gallery](
	[id] [int] IDENTITY(1,1) NOT NULL,
	[image_path] [nvarchar](500) NOT NULL,
	[category] [nvarchar](100) NULL,
	[description] [nvarchar](500) NULL,
	[display_order] [int] NOT NULL,
	[is_active] [bit] NOT NULL,
	[created_at] [datetime2](7) NOT NULL,
PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[measurements]    Script Date: 14-09-2026 16:20:48 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[measurements](
	[id] [int] IDENTITY(1,1) NOT NULL,
	[customer_id] [int] NOT NULL,
	[version] [int] NOT NULL,
	[blouse_length] [decimal](6, 2) NULL,
	[shoulder] [decimal](6, 2) NULL,
	[bust] [decimal](6, 2) NULL,
	[waist] [decimal](6, 2) NULL,
	[armhole] [decimal](6, 2) NULL,
	[sleeve_length] [decimal](6, 2) NULL,
	[sleeve_round] [decimal](6, 2) NULL,
	[neck_front] [decimal](6, 2) NULL,
	[neck_back] [decimal](6, 2) NULL,
	[neck_width] [decimal](6, 2) NULL,
	[neck_depth] [decimal](6, 2) NULL,
	[other_notes] [nvarchar](1000) NULL,
	[is_current] [bit] NOT NULL,
	[created_at] [datetime2](7) NOT NULL,
PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY],
 CONSTRAINT [UQ_customer_version] UNIQUE NONCLUSTERED 
(
	[customer_id] ASC,
	[version] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[order_images]    Script Date: 14-09-2026 16:20:48 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[order_images](
	[id] [int] IDENTITY(1,1) NOT NULL,
	[order_id] [int] NULL,
	[customer_id] [int] NULL,
	[image_type] [nvarchar](30) NOT NULL,
	[file_name] [nvarchar](255) NOT NULL,
	[file_path] [nvarchar](500) NOT NULL,
	[uploaded_by] [nvarchar](100) NULL,
	[uploaded_at] [datetime2](7) NOT NULL,
	[is_active] [bit] NOT NULL,
PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[order_status_history]    Script Date: 14-09-2026 16:20:48 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[order_status_history](
	[id] [int] IDENTITY(1,1) NOT NULL,
	[order_id] [int] NULL,
	[previous_status] [nvarchar](30) NULL,
	[new_status] [nvarchar](30) NOT NULL,
	[remarks] [nvarchar](500) NULL,
	[updated_by] [nvarchar](100) NULL,
	[created_at] [datetime2](7) NOT NULL
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[orders]    Script Date: 14-09-2026 16:20:48 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[orders](
	[id] [int] IDENTITY(1,1) NOT NULL,
	[order_number] [nvarchar](30) NOT NULL,
	[customer_id] [int] NOT NULL,
	[design_id] [int] NOT NULL,
	[measurement_id] [int] NOT NULL,
	[customisation_notes] [nvarchar](1000) NULL,
	[total_amount] [decimal](10, 2) NOT NULL,
	[amount_received] [decimal](10, 2) NOT NULL,
	[amount_pending] [decimal](10, 2) NOT NULL,
	[payment_mode] [nvarchar](30) NULL,
	[payment_status] [nvarchar](20) NOT NULL,
	[delivery_date] [date] NULL,
	[status] [nvarchar](30) NOT NULL,
	[cancellation_reason] [nvarchar](500) NULL,
	[created_at] [datetime2](7) NOT NULL,
	[updated_at] [datetime2](7) NOT NULL,
PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY],
UNIQUE NONCLUSTERED 
(
	[order_number] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[payments]    Script Date: 14-09-2026 16:20:48 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[payments](
	[id] [int] IDENTITY(1,1) NOT NULL,
	[order_id] [int] NOT NULL,
	[amount] [decimal](10, 2) NOT NULL,
	[mode] [nvarchar](30) NULL,
	[reference_no] [nvarchar](100) NULL,
	[status] [nvarchar](20) NOT NULL,
	[verified_by] [nvarchar](100) NULL,
	[created_at] [datetime2](7) NOT NULL,
PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[website_settings]    Script Date: 14-09-2026 16:20:48 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[website_settings](
	[setting_key] [nvarchar](100) NOT NULL,
	[setting_value] [nvarchar](max) NULL,
PRIMARY KEY CLUSTERED 
(
	[setting_key] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO
ALTER TABLE [dbo].[admin_users] ADD  DEFAULT ((1)) FOR [is_active]
GO
ALTER TABLE [dbo].[admin_users] ADD  DEFAULT ((0)) FOR [failed_attempts]
GO
ALTER TABLE [dbo].[admin_users] ADD  DEFAULT (sysutcdatetime()) FOR [created_at]
GO
ALTER TABLE [dbo].[audit_logs] ADD  DEFAULT (sysutcdatetime()) FOR [created_at]
GO
ALTER TABLE [dbo].[customers] ADD  DEFAULT ((1)) FOR [is_active]
GO
ALTER TABLE [dbo].[customers] ADD  DEFAULT (sysutcdatetime()) FOR [created_at]
GO
ALTER TABLE [dbo].[designs] ADD  DEFAULT ((0)) FOR [base_price]
GO
ALTER TABLE [dbo].[designs] ADD  DEFAULT ((0)) FOR [additional_charges]
GO
ALTER TABLE [dbo].[designs] ADD  DEFAULT ('ACTIVE') FOR [status]
GO
ALTER TABLE [dbo].[designs] ADD  DEFAULT (sysutcdatetime()) FOR [created_at]
GO
ALTER TABLE [dbo].[designs] ADD  DEFAULT (sysutcdatetime()) FOR [modified_at]
GO
ALTER TABLE [dbo].[email_logs] ADD  DEFAULT (sysutcdatetime()) FOR [sent_at]
GO
ALTER TABLE [dbo].[email_logs] ADD  DEFAULT ((0)) FOR [retry_count]
GO
ALTER TABLE [dbo].[gallery] ADD  DEFAULT ((0)) FOR [display_order]
GO
ALTER TABLE [dbo].[gallery] ADD  DEFAULT ((1)) FOR [is_active]
GO
ALTER TABLE [dbo].[gallery] ADD  DEFAULT (sysutcdatetime()) FOR [created_at]
GO
ALTER TABLE [dbo].[measurements] ADD  DEFAULT ((1)) FOR [is_current]
GO
ALTER TABLE [dbo].[measurements] ADD  DEFAULT (sysutcdatetime()) FOR [created_at]
GO
ALTER TABLE [dbo].[order_images] ADD  DEFAULT (sysutcdatetime()) FOR [uploaded_at]
GO
ALTER TABLE [dbo].[order_images] ADD  DEFAULT ((1)) FOR [is_active]
GO
ALTER TABLE [dbo].[order_status_history] ADD  DEFAULT (sysutcdatetime()) FOR [created_at]
GO
ALTER TABLE [dbo].[orders] ADD  DEFAULT ((0)) FOR [total_amount]
GO
ALTER TABLE [dbo].[orders] ADD  DEFAULT ((0)) FOR [amount_received]
GO
ALTER TABLE [dbo].[orders] ADD  DEFAULT ((0)) FOR [amount_pending]
GO
ALTER TABLE [dbo].[orders] ADD  DEFAULT ('PENDING') FOR [payment_status]
GO
ALTER TABLE [dbo].[orders] ADD  DEFAULT ('ORDER_RECEIVED') FOR [status]
GO
ALTER TABLE [dbo].[orders] ADD  DEFAULT (sysutcdatetime()) FOR [created_at]
GO
ALTER TABLE [dbo].[orders] ADD  DEFAULT (sysutcdatetime()) FOR [updated_at]
GO
ALTER TABLE [dbo].[payments] ADD  DEFAULT ('PENDING') FOR [status]
GO
ALTER TABLE [dbo].[payments] ADD  DEFAULT (sysutcdatetime()) FOR [created_at]
GO
ALTER TABLE [dbo].[email_logs]  WITH CHECK ADD FOREIGN KEY([customer_id])
REFERENCES [dbo].[customers] ([id])
GO
ALTER TABLE [dbo].[email_logs]  WITH CHECK ADD FOREIGN KEY([order_id])
REFERENCES [dbo].[orders] ([id])
GO
ALTER TABLE [dbo].[measurements]  WITH CHECK ADD FOREIGN KEY([customer_id])
REFERENCES [dbo].[customers] ([id])
GO
ALTER TABLE [dbo].[order_images]  WITH CHECK ADD FOREIGN KEY([customer_id])
REFERENCES [dbo].[customers] ([id])
GO
ALTER TABLE [dbo].[order_images]  WITH CHECK ADD FOREIGN KEY([order_id])
REFERENCES [dbo].[orders] ([id])
GO
ALTER TABLE [dbo].[order_status_history]  WITH CHECK ADD FOREIGN KEY([order_id])
REFERENCES [dbo].[orders] ([id])
GO
ALTER TABLE [dbo].[orders]  WITH CHECK ADD FOREIGN KEY([customer_id])
REFERENCES [dbo].[customers] ([id])
GO
ALTER TABLE [dbo].[orders]  WITH CHECK ADD FOREIGN KEY([design_id])
REFERENCES [dbo].[designs] ([id])
GO
ALTER TABLE [dbo].[orders]  WITH CHECK ADD FOREIGN KEY([measurement_id])
REFERENCES [dbo].[measurements] ([id])
GO
ALTER TABLE [dbo].[payments]  WITH CHECK ADD FOREIGN KEY([order_id])
REFERENCES [dbo].[orders] ([id])
GO

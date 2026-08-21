INSERT INTO "Tenants"
    ("Id", "Name", "Domain", "Platform", "Status", "Plan", "CreatedAt", "UpdatedAt")
VALUES
    ('cccccccc-cccc-cccc-cccc-cccccccccccc', 'Legacy Store', 'legacy.example',
     'shopify', 'active', 'starter', now(), now());

INSERT INTO "Users"
    ("Id", "Email", "DisplayName", "Role", "TenantId", "CreatedAt", "UpdatedAt",
     "PasswordHash", "TokenVersion")
VALUES
    ('c1000000-0000-0000-0000-000000000001', 'Legacy.Admin@Example.COM',
     'Legacy Admin', 'merchant_admin', 'cccccccc-cccc-cccc-cccc-cccccccccccc',
     now(), now(), 'pbkdf2-sha256.1.YQ==.Yg==', 0);

INSERT INTO "Accounts"
    ("Id", "Name", "Slug", "BillingEmail", "Status", "CreatedAt", "UpdatedAt")
VALUES
    ('c2000000-0000-0000-0000-000000000001', 'Legacy Account', 'legacy-account',
     'billing@legacy.example', 'active', now(), now());

INSERT INTO "Stores"
    ("Id", "AccountId", "Name", "Slug", "Platform", "Domain", "Status",
     "CreatedAt", "UpdatedAt")
VALUES
    ('c3000000-0000-0000-0000-000000000001',
     'c2000000-0000-0000-0000-000000000001', 'Legacy Store', 'legacy-store',
     'shopify', 'legacy.example', 'active', now(), now());

INSERT INTO "Garments"
    ("Id", "TenantId", "ExternalProductId", "Name", "Category", "Layer",
     "SourceImageUrl", "IsActive", "IsDeleted", "CreatedAt", "UpdatedAt")
VALUES
    ('c4000000-0000-0000-0000-000000000001',
     'cccccccc-cccc-cccc-cccc-cccccccccccc', 'legacy-product', 'Legacy Garment',
     'top', 'top', 'https://example.com/legacy.png', true, false, now(), now());

INSERT INTO "GarmentAssets"
    ("Id", "TenantId", "GarmentId", "AssetType", "SourceImageUrl",
     "ConfidenceScore", "CreatedAt")
VALUES
    ('c5000000-0000-0000-0000-000000000001',
     'cccccccc-cccc-cccc-cccc-cccccccccccc',
     'c4000000-0000-0000-0000-000000000001', 'front',
     'https://example.com/legacy.png', 1, now());

INSERT INTO "AssetVersions"
    ("Id", "GarmentAssetId", "VersionNumber", "ProcessingModel", "CreatedAt")
VALUES
    ('c6000000-0000-0000-0000-000000000001',
     'c5000000-0000-0000-0000-000000000001', 1, 'legacy-model', now());

INSERT INTO "Avatars"
    ("Id", "UserId", "TenantId", "Source", "HeightCm", "WeightKg", "Age",
     "Gender", "IsPregnant", "SkinTone", "SmplParametersJson", "CreatedAt", "UpdatedAt")
VALUES
    ('c7000000-0000-0000-0000-000000000001',
     'c1000000-0000-0000-0000-000000000001', NULL, 'legacy-avatar', 172, 70,
     30, 'neutral', false, 'neutral', '{}', now(), now());

INSERT INTO "UserLooks"
    ("Id", "UserId", "AvatarId", "TenantId", "Mode", "SnapshotUrl",
     "MetadataJson", "CreatedAt")
VALUES
    ('cb000000-0000-0000-0000-000000000001',
     'c1000000-0000-0000-0000-000000000001',
     'c7000000-0000-0000-0000-000000000001', NULL, 'legacy',
     'https://example.com/look.png', '{}', now());

INSERT INTO "RenderJobs"
    ("Id", "TenantId", "AvatarId", "GarmentAssetId", "AssetVersionId", "Status",
     "AttemptCount", "IsDeleted", "CreatedAt", "UpdatedAt")
VALUES
    ('c8000000-0000-0000-0000-000000000001',
     'cccccccc-cccc-cccc-cccc-cccccccccccc',
     'c7000000-0000-0000-0000-000000000001',
     'c5000000-0000-0000-0000-000000000001',
     'c6000000-0000-0000-0000-000000000001', 'completed', 1, false, now(), now());

INSERT INTO "RenderResults"
    ("Id", "RenderJobId", "OutputImageUrl", "PreviewImageUrl", "IsDeleted", "CreatedAt")
VALUES
    ('c9000000-0000-0000-0000-000000000001',
     'c8000000-0000-0000-0000-000000000001',
     'https://example.com/output.png', 'https://example.com/preview.png', false, now());

INSERT INTO "MerchantAdminSettings"
    ("Id", "TenantId", "SupportEmail", "WebsiteUrl", "ApiKey", "WebhookUrl",
     "CreatedAt", "UpdatedAt")
VALUES
    ('ca000000-0000-0000-0000-000000000001',
     'cccccccc-cccc-cccc-cccc-cccccccccccc', 'support@legacy.example',
     'https://legacy.example', 'tv_live_plaintext_legacy',
     'https://legacy.example/webhooks', now(), now());

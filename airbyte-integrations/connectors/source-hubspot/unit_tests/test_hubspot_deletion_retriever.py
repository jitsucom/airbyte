#
# Copyright (c) 2025 Airbyte, Inc., all rights reserved.
#
"""Unit test for HubspotDeletionRetriever: an archived record becomes a tombstone."""

components_module = __import__("components")
HubspotDeletionRetriever = components_module.HubspotDeletionRetriever

ARCHIVED_AT = "2024-05-01T10:00:00.000Z"

# Plain string schema so normalization is a no-op and the archivedAt string is preserved verbatim.
RECORDS_SCHEMA = {
    "type": "object",
    "additionalProperties": True,
    "properties": {
        "id": {"type": ["null", "string"]},
        "updatedAt": {"type": ["null", "string"]},
        "archivedAt": {"type": ["null", "string"]},
        "_ab_cdc_deleted_at": {"type": ["null", "string"]},
        "properties_name": {"type": ["null", "string"]},
    },
}


class _FakeArchivedRetriever:
    def __init__(self, records):
        self._records = records

    def read_records(self, records_schema, stream_slice=None):
        for record in self._records:
            yield dict(record)


class _NoopLiveRetriever:
    def read_records(self, records_schema, stream_slice=None):
        return iter(())


def test_archived_record_becomes_tombstone():
    archived = {
        "id": "99",
        "archived": True,
        "createdAt": "2023-01-01T00:00:00.000Z",
        "archivedAt": ARCHIVED_AT,
        "properties": {"name": "Deleted Co"},
    }
    retriever = HubspotDeletionRetriever(
        live_retriever=_NoopLiveRetriever(),
        config={},
        parameters={},
        archived_retriever=_FakeArchivedRetriever([archived]),
    )

    tombstones = list(retriever._read_archived_records(RECORDS_SCHEMA))

    assert len(tombstones) == 1
    tombstone = tombstones[0]
    assert tombstone["id"] == "99"
    # archivedAt drives both the deletion marker and the dedup cursor.
    assert tombstone["_ab_cdc_deleted_at"] == ARCHIVED_AT
    assert tombstone["updatedAt"] == ARCHIVED_AT
    assert tombstone["archivedAt"] == ARCHIVED_AT
    # Full flattened property columns are present (not a sparse record).
    assert tombstone["properties_name"] == "Deleted Co"

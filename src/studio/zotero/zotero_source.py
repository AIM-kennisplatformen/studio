from typing import Any, Final

from dotenv import load_dotenv
from loguru import logger

from pyzotero import zotero
import os

# pylint: disable-next=too-few-public-methods
class ZoteroSource:
    def __init__(self) -> None:
        load_dotenv()
        self.zotero = zotero.Zotero(
            library_id=os.getenv("ZOTERO_LIBRARY_ID"),
            library_type="user",
            api_key=os.getenv("ZOTERO_API_KEY"),
            local=True,
        )
    async def get_all_collection_items(
        self,
        *,
        collection_name: str,
    ) -> list[dict[str, Any]]:
        result = self._zotero.zotero.collections(q=collection_name)
        if not result:
            return []

        collection_id = result[0]["key"]
        collection_items = self._zotero.zotero.everything(
            self._zotero.zotero.collection_items_top(collection_id, limit=None)
        )
        return collection_items

    async def extract_zotero_metadata(
        self,
        *,
        query: str,
    ) -> list[str] | None:
        """Extract metadata for a document title

        Args:
            `title`: The title of the document for which the metadata needs to be extracted

        Returns:
            metadata or Zotero errors
        """
        logger.debug("Fetching metadata from zotero for documents (query: {})", query)
        results = self.zotero.items(q=query)
        logger.debug("Zotero results: {}", len(results))

        """
        for item in results:
            title = item['data'].get('title', 'No title')
            item_type = item['data'].get('itemType', 'Unknown type')
            date = item['data'].get('date', 'No date')
            item_id = item['data'].get('key', 'No ID')
        """

        # todo fetch forbidden UserNotAuthorisedError

        return results

    async def download_zotero_item(
        self,
        *,
        item_id: str,
        path: str,
    ) -> None:
        logger.debug("Fetching File: %s", item_id)
        children = self._zotero.zotero.children(item_id)

        if not children:
            logger.warning("No child attachments found for item %s", item_id)
            return  # nothing to download

        # optionally filter to only attachments
        attachments = [
            c for c in children if c.get("data", {}).get("itemType") == "attachment"
        ]

        if not attachments:
            logger.warning("No attachment-type children for item %s", item_id)
            return

        attachment = attachments[0]  # safe now
        data = attachment.get("data", {})
        file_path = data.get("path")

        if not file_path:
            logger.warning("Attachment for item %s has no local path", item_id)
            return

        print(file_path)
        self._zotero.zotero.dump(
            itemkey=attachment["key"],
            filename=f"{item_id}.pdf",
            path=path,
        )

    async def extract_zotero_metadata(
        self,
        *,
        query: str,
    ) -> list[str] | None:
        """Extract metadata for a document title

        Args:
            `title`: The title of the document for which the metadata needs to be extracted

        Returns:
            metadata or Zotero errors
        """
        logger.debug("Fetching metadata from zotero for documents (query: {})", query)
        results = self._zotero.zotero.items(q=query)
        logger.debug("Zotero results: {}", len(results))

        '''
        for item in results:
            title = item['data'].get('title', 'No title')
            item_type = item['data'].get('itemType', 'Unknown type')
            date = item['data'].get('date', 'No date')
            item_id = item['data'].get('key', 'No ID')
        ''' 

        #todo fetch forbidden UserNotAuthorisedError

        return results
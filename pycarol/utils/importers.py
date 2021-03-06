import pandas as pd
from dask import dataframe as dd
import multiprocessing
import functools
import warnings

from tqdm import tqdm

__STAGING_FIELDS = ['mdmCounterForEntity', 'mdmId']
__DM_FIELDS = ['mdmCounterForEntity', 'mdmId']


def _import_dask(storage, merge_records=False,
                 dm_name=None, import_type='staging', return_dask_graph=False,
                 connector_id=None, staging_name=None, view_name=None, columns=None,
                 max_hits=None, mapping_columns=None):
    if columns:
        columns = list(set(columns))
        columns += __STAGING_FIELDS
        columns = list(set(columns))

    if import_type=='golden':
        url = [storage.build_url_parquet_golden(dm_name=dm_name)]
    elif import_type == 'staging':
        url = []
        url1 = storage.build_url_parquet_staging(staging_name=staging_name, connector_id=connector_id)
        if url1 is not None:
            url.append(url1)

        url2 = storage.build_url_parquet_staging_master(staging_name=staging_name, connector_id=connector_id)
        if url2 is not None:
            url.append(url2)

        url3 = storage.build_url_parquet_staging_rejected(staging_name=staging_name, connector_id=connector_id)
        if url3 is not None:
            url.append(url3)
    elif import_type == 'view':
        url = [storage.build_url_parquet_view(view_name=view_name)]
    else:
        raise KeyError('import_type should be `golden`,`staging` or `view`')



    d = dd.read_parquet(url, storage_options=storage.get_dask_options(), columns=columns)

    d= d.rename(columns=mapping_columns)
    if return_dask_graph:
        return d
    else:
        return d.compute()


def _import_pandas(storage, dm_name=None, connector_id=None, columns=None, mapping_columns=None, max_workers=None,
                   staging_name=None, view_name=None, import_type='staging', golden=False, max_hits=None, callback=None,
                   token_carolina=None, storage_space=None,  file_pattern=None):
    if columns:
        columns = list(set(columns))
        columns += __DM_FIELDS
        columns = list(set(columns))

    if import_type=='golden':
        file_paths = storage.get_golden_file_paths(dm_name=dm_name)
    elif import_type=='staging':
        file_paths = storage.get_staging_file_paths(staging_name=staging_name, connector_id=connector_id)
    elif import_type == 'view':
        file_paths = storage.get_view_file_paths(view_name=view_name)
    elif import_type == 'staging_cds':
        file_paths = storage.get_staging_cds_file_paths(staging_name=staging_name, connector_id=connector_id,
                                                        file_pattern=file_pattern)
    elif import_type == 'golden_cds':
        file_paths = storage.get_golden_cds_file_paths(dm_name=dm_name,
                                                       file_pattern=file_pattern)
    elif import_type == 'view_cds':
        file_paths = storage.get_view_cds_file_paths(dm_name=view_name)
    else:
        raise KeyError('import_type should be `golden`,`staging`, `view`, `staging_cds`, `golden_cds`, `view_cds`')

    df_list = []
    count = 0


    if max_workers is not None:
        assert max_workers > 0, f"max_workers must be greater than zero, you passed {max_workers}"
    else:
        max_workers = 1

    if max_workers > 1:
        client = _load_client(token_carolina)
        if max_hits:
            warnings.warn("max_hits does not work when max_hits>1", DeprecationWarning)
        partial_download = functools.partial(_download_files, storage=client, storage_space=storage_space,
                                             columns=columns,
                                             mapping_columns=mapping_columns, callback=callback)
        with multiprocessing.Pool(processes=max_workers) as pool:
            df_list = pool.map(partial_download, file_paths)
    else:
        for i, file in enumerate(tqdm(file_paths)):
            buffer = storage.load(file['name'], format='raw', cache=False, storage_space=file['storage_space'])
            result = pd.read_parquet(buffer, columns=columns)

            if mapping_columns is not None:
                # fix columns names (we replace `-` for `_` due to parquet limitations.
                result.rename(columns=mapping_columns, inplace=True)
            if callback:
                assert callable(callback), \
                    f'"{callback}" is a {type(callback)} and is not callable. This variable must be a function/class.'
                result = callback(result)

            df_list.append(result)
            if max_hits is not None:
                count_old = count
                count += len(df_list[i])
                if count >= max_hits:
                    df_list[i] = df_list[i].iloc[:max_hits - count_old]
                    break
    if not df_list:
        return None
    return pd.concat(df_list, ignore_index=True, sort=True)



def _download_files(file, storage, storage_space, columns, mapping_columns, callback):
    filename = storage_space +'/' + file['name']
    buffer = storage.open(filename)
    result = pd.read_parquet(buffer, columns=columns)

    if mapping_columns is not None:
        result.rename(columns=mapping_columns, inplace=True)

    if callback:
        result = callback(result)
    return result

def _load_client(token):
    import gcsfs
    client = gcsfs.GCSFileSystem(token=token)
    return client

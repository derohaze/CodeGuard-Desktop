use std::cmp::Ordering;

use crate::config::HOTSPOT_LIMIT;
use crate::model::{HotspotFile, NativeIndex};

pub fn push_bounded_hotspot(index: &mut NativeIndex, hotspot: HotspotFile) {
    if index.hotspot_files.len() < HOTSPOT_LIMIT {
        index.hotspot_files.push(hotspot);
        return;
    }

    if let Some((weakest_index, weakest)) = index.hotspot_files.iter().enumerate().min_by(compare_weakest_first) {
        if hotspot.score > weakest.score
            || (hotspot.score == weakest.score && hotspot.file.as_str() < weakest.file.as_str())
        {
            index.hotspot_files[weakest_index] = hotspot;
        }
    }
}

pub fn sort_hotspots(hotspots: &mut [HotspotFile]) {
    hotspots.sort_by(compare_strongest_first);
}

fn compare_weakest_first(
    (_, left): &(usize, &HotspotFile),
    (_, right): &(usize, &HotspotFile),
) -> Ordering {
    left.score
        .cmp(&right.score)
        .then_with(|| right.file.as_str().cmp(left.file.as_str()))
}

fn compare_strongest_first(left: &HotspotFile, right: &HotspotFile) -> Ordering {
    right.score
        .cmp(&left.score)
        .then_with(|| left.file.as_str().cmp(right.file.as_str()))
}

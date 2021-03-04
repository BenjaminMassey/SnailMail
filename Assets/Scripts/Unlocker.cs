using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Runtime.Serialization.Formatters.Binary;
using UnityEngine;
using UnityEngine.UI;

public class Unlocker : MonoBehaviour
{
    // Start is called before the first frame update
    void Start()
    {
        Unlocks.file_path = Application.persistentDataPath + "/snailmail.save";
        if (!Unlocks.initialized)
        {
            Unlocks.level_done[0] = true;
            for (int i = 1; i < Unlocks.num_levels; i++)
            {
                Unlocks.level_done[i] = false;
            }
            Unlocks.initialized = true;
        }
        Unlocks.LoadData();
        UpdateButtons();
    }

    public void UpdateButtons()
    {
        int start_point = GameObject.Find("Canvas").GetComponent<PageHandler>().page * 10;
        int end_point = start_point + 10;
        end_point = Mathf.Min(Unlocks.num_levels, end_point);
        //Debug.Log("start_point: " + start_point + " | end_point: " + end_point);
        for (int i = start_point; i < end_point; i++)
        {
            string button_name = "Level" + (i + 1) + " Button";
            GameObject level_button_obj = GameObject.Find(button_name);
            //Debug.Log("Trying to use button: " + button_name);
            Button level_button = level_button_obj.GetComponent<Button>();
            level_button.enabled = Unlocks.level_done[i];
            if (Unlocks.level_done[i])
            {
                level_button_obj.GetComponent<Image>().color = new Color(1.0f, 1.0f, 1.0f);
            }
            else
            {
                level_button_obj.GetComponent<Image>().color = new Color(0.25f, 0.25f, 0.25f);
                level_button_obj.transform.GetChild(0).GetComponent<Text>().color = new Color(0, 0, 0);
            }
        }
    }
}

public static class Unlocks
{
    public static bool initialized = false;
    public static int num_levels = 19;
    public static bool[] level_done = new bool[num_levels];
    public static string file_path;

    public static void SaveData()
    {
        Debug.Log("Attempting save data (" + file_path + ")");
        // https://support.unity3d.com/hc/en-us/articles/115000341143/comments/360000857792
        try
        {
            using (StreamWriter sw = new StreamWriter(new FileStream(file_path, FileMode.OpenOrCreate, FileAccess.Write)))
            {
                string data = "";
                for (int i = 0; i < num_levels; i++)
                {
                    data += level_done[i] ? "1" : "0";
                }
                sw.Write(data);
                sw.Close();
            }
        }
        catch (Exception e)
        {
            Debug.Log(e.ToString());
        }
    }

    public static void LoadData()
    {
        Debug.Log("Attempting load data (" + file_path + ")");
        if (File.Exists(file_path))
        {
            Debug.Log("Succeeded file open: data collecting");
            try
            {
                using (StreamReader sr = new StreamReader(new FileStream(file_path, FileMode.Open, FileAccess.Read)))
                {
                    int i = 0;
                    while (sr.Peek() >= 0)
                    {
                        if (i >= num_levels) { break; }
                        try
                        {
                            char c = (char)sr.Read();
                            //Debug.Log("CHAR READ: " + c.ToString());
                            level_done[i] = c == '1';
                        }
                        catch (Exception)
                        {
                            level_done[i] = false;
                        }
                        i++;
                    }

                    sr.Close();
                }
            }
            catch (Exception e) { Debug.Log(e.ToString()); }
        }
        else
        {
            Debug.Log("Failed file open: creating new one");
            SaveData();
        }
    }

    public static void ResetData()
    {
        level_done[0] = true;
        for (int i = 1; i < num_levels; i++)
        {
            level_done[i] = false;
        }
        SaveData();
    }
}
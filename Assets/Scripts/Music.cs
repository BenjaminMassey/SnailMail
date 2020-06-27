// BASE STOLEN FROM: http://answers.unity.com/answers/1260412/view.html

using UnityEngine;

public class Music : MonoBehaviour
{
    // Play on awake handles the actual playing

    private void Awake()
    {
        int count = GameObject.FindGameObjectsWithTag("Music").Length;
        if (count > 1)
        {
            Destroy(gameObject);
        }
        DontDestroyOnLoad(transform.gameObject);
    }
}